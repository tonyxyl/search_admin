# coding=utf-8

from flask_restful import Resource, reqparse
from flask import Response, request
from .decorator import check_http_headers, check_request_frequency
from app.models import User, Token, Website
from elasticsearch import Elasticsearch
from elasticsearch_dsl.search import Search
from .. import flask_redis
from re import match, split
from time import time
from ..utils import hash_sha256

# es连接实例
client = Elasticsearch(hosts=['127.0.0.1:9200'], timeout=30000)

# 相关搜索
def related_search(es_client, keyword, field='suggest', size=6):
	es_related_options = {
		"suggest": {
			"prefix": keyword,
			"completion": {
				"field": field,
				"size": size
			}
		}
	}
	try:
		rs = es_client.suggest(index='related', body=es_related_options)
		return rs
	except Exception as e:
		return ''

# 数值限制
def num_limit(value, name):
	if value.isdigit() is False:
		raise ValueError("{0} 必须是整数".format(name))
	elif int(value) < 1:
		raise ValueError("{0} 不能小于1".format(name))
	elif int(value) > 50:
		raise ValueError("{0} 不能大于50".format(name))
	else:
		return value

# 日期限制
def date_limit(value, name):
	if match(r'^(?:(?!0000)[0-9]{4}-(?:(?:0[1-9]|1[0-2])-(?:0[1-9]|1[0-9]|2[0-8])|(?:0[13-9]|1[0-2])-(?:29|30)|(?:0[13578]|1[02])-31)|(?:[0-9]{2}(?:0[48]|[2468][048]|[13579][26])|(?:0[48]|[2468][048]|[13579][26])00)-02-29)$', value):
		return value
	else:
		raise ValueError("{0} 必须是有效的日期格式yyyy-mm-dd".format(name))

# 排序字段限制
def sort_limit(value):
	if value in ['pdate', 'channel', 'category', 'has_pic', 'has_video', 'author', 'origin']:
		return value
	else:
		return '_score'

def sort_2_limit(value):
	if value in ['category', 'years', 'channel', 'location', 'times']:
		return value
	else:
		return '_score'

# 排序顺序限制
def order_limt(value):
	if value == 'desc':
		return '-'
	else:
		return ''

# 过滤字段限制
def filter_limit(value, name):
	if value in ['url', 'title']:
		return value
	else:
		raise ValueError("{0} 只能是url或title".format(name))

class SuggestApi(Resource):
	decorators = [check_http_headers, check_request_frequency,]
	def __init__(self):
		super(SuggestApi, self).__init__()
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('_', type=int, help='时间戳不能空', required=True)
		self.parser.add_argument('appkey', type=str, help='appkey不能空', required=True)
		self.parser.add_argument('token', type=str, help='token不能空', required=True)
		self.parser.add_argument('sign', type=str, help='sign不能空', required=True)
		self.parser.add_argument('keyword', type=str, required=True, help='关键词')
		self.args = self.parser.parse_args()

	def post(self):
		ts = self.args['_']
		if abs(int(time() * 1000) - int(ts)) > 1800000:
			return {'success':0, 'message': '时间戳无效'}, 200
		token = self.args['token']
		appkey = self.args['appkey']
		verify_token = flask_redis.get(appkey)
		if verify_token is None:
			return {'success': 0, 'message': 'token 无效'}, 200
		else:
			verify_token = verify_token.decode('utf-8') if type(verify_token) == type(b'') else verify_token
			if verify_token != token:
				return {'success': 0, 'message': 'token 无效'}, 200
		sign = self.args['sign']
		if hash_sha256("{0},{1},{2}".format(ts, token, appkey)) != sign:
			return {'success': 0, 'message': 'sign 无效'}, 200
		keyword = self.args['keyword']
		query = Website.query.join(Token, Website.id==Token.website_id).filter(Token.appkey == appkey).first()
		domain = query.domain
		try:
			s = Search(using=client, index='suggest', doc_type='news')
			s = s.filter('term', website=domain).query('match', title=keyword)
			s = s[0:10]
			response = s.execute()
			return {'success': 1, 'data': response.to_dict()}, 200
		except Exception as e:
			return {'success': 0, 'message': e}, 200
		#return request.data.decode('utf-8')

class TokenApi(Resource):
	decorators = [check_http_headers, check_request_frequency,]
	def __init__(self):
		super(TokenApi, self).__init__()
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('_', type=int, help='时间戳不能空', required=True)
		self.parser.add_argument('appkey', type=str, required=True, help='appkey 不能空')
		self.parser.add_argument('appsecret', type=str, required=True, help='appsecret 不能空')
		self.args = self.parser.parse_args()

	def post(self):
		ts = self.args['_']
		if abs(int(time() * 1000) - int(ts)) > 1800000:
			return {'success':0, 'message': '时间戳无效'}, 200
		appkey = self.args['appkey']
		appsecret = self.args['appsecret']
		auth =Token.query.filter(Token.appkey == appkey, Token.appsecret == appsecret).first()
		if auth is not None:
			token = flask_redis.get(appkey)
			if token is None:
				token = hash_sha256("{0}-{1}".format(appkey, ts))
				flask_redis.setex(appkey, 1800, token)
			token = token if type(token) != type(b'') else token.decode('utf-8')
			expires = flask_redis.ttl(appkey)
			return {'success': 1, 'data': {'token':token, 'expires': expires}}, 200
		else:
			return {'success': 0, 'message': '授权未通过'}, 200

class SearchApi(Resource):
	decorators = [check_http_headers, check_request_frequency,]
	def __init__(self):
		super(SearchApi, self).__init__()
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('_', type=int, help='时间戳不能空', required=True)
		self.parser.add_argument('appkey', type=str, help='appkey不能空', required=True)
		self.parser.add_argument('token', type=str, help='token不能空', required=True)
		self.parser.add_argument('sign', type=str, help='sign不能空', required=True)
		self.parser.add_argument('page', type=num_limit, default=1)
		self.parser.add_argument('size', type=num_limit, default=10)
		self.parser.add_argument('channel', type=str, help='频道')
		self.parser.add_argument('category', type=str, help='类别')
		self.parser.add_argument('origin', type=str, help='来源')
		self.parser.add_argument('has_pic', type=str, help='是否有图') #为空则false, 否则true
		self.parser.add_argument('has_video', type=str, help='是否有视频')
		self.parser.add_argument('author', type=str, help='作者')
		self.parser.add_argument('editor', type=str, help='编辑')
		self.parser.add_argument('v1', type=str, help='预留字段1')
		self.parser.add_argument('v2', type=str, help='预留字段2')
		self.parser.add_argument('v3', type=str, help='预留字段3')
		self.parser.add_argument('v4', type=str, help='预留字段4')
		self.parser.add_argument('v5', type=str, help='预留字段5')
		self.parser.add_argument('v6', type=str, help='预留字段6')
		self.parser.add_argument('s', type=sort_limit, help='排序字段', default='_score')
		self.parser.add_argument('o', type=order_limt, help='排序顺序', default='')
		self.parser.add_argument('f', type=filter_limit, help='过滤字段')
		self.parser.add_argument('l', type=str, help='过滤列表,用逗号分隔')
		self.parser.add_argument('scope', type=str, help='搜索范围', default='')
		self.parser.add_argument('from', type=date_limit, help='起始日期', default='1996-01-01')
		self.parser.add_argument('to', type=date_limit, help='结束日期', default='2038-01-01')
		self.parser.add_argument('keyword', type=str, required=True, help='关键词')
		self.parser.add_argument('not', type=str, help='非关键词')
		self.parser.add_argument('and', type=str, help='与关键词')
		self.args = self.parser.parse_args()

	def post(self):
		ts = self.args['_']
		if abs(int(time() * 1000) - int(ts)) > 1800000:
			return {'success':0, 'message': '时间戳无效'}, 200
		token = self.args['token']
		appkey = self.args['appkey']
		verify_token = flask_redis.get(appkey)
		if verify_token is None:
			return {'success': 0, 'message': 'token 无效'}, 200
		else:
			verify_token = verify_token.decode('utf-8') if type(verify_token) == type(b'') else verify_token
			if verify_token != token:
				return {'success': 0, 'message': 'token 无效'}, 200
		sign = self.args['sign']
		if hash_sha256("{0},{1},{2}".format(ts, token, appkey)) != sign:
			return {'success': 0, 'message': 'sign 无效'}, 200
		query = Website.query.join(Token, Website.id==Token.website_id).filter(Token.appkey == appkey).first()
		domain = query.domain
		page = int(self.args['page'])
		size = int(self.args['size'])
		from_size = (page - 1) * size
		to_size = page * size
		origin = self.args['origin']
		channel = self.args['channel']
		category = self.args['category']
		author = self.args['author']
		editor = self.args['editor']
		begin = self.args['from']
		to = self.args['to']
		has_pic = self.args['has_pic']
		has_video = self.args['has_video']
		v1 = self.args['v1']
		v2 = self.args['v2']
		v3 = self.args['v3']
		v4 = self.args['v4']
		v5 = self.args['v5']
		v6 = self.args['v6']
		not_ = self.args['not']
		and_ = self.args['and']
		sort_field = self.args['s']
		o = self.args['o']
		f = self.args['f']
		l = self.args['l']
		l = [] if l is None else l.split(',')
		scope = self.args['scope']
		if scope in ['content', 'tag', 'title', 'description']:
			scope = [scope]
		else:
			scope = ['content', 'tag', 'title', 'description']
		keyword = self.args['keyword']
		try:
			s = Search(using=client, index='common', doc_type='search')
			s = s.filter('term', website=domain)
			if author:
				s = s.filter('term', author=author)
			if editor:
				s = s.filter('term', editor=editor)
			if origin:
				s = s.filter('term', origin=origin)
			if category:
				s = s.filter('term', category=category)
			if channel:
				s = s.filter('term', channel=channel)
			if v1:
				s = s.filter('term', reserved_1=v1)
			if v2:
				s = s.filter('term', reserved_2=v2)
			if v3:
				s = s.filter('term', reserved_3=v3)
			if v4:
				s = s.filter('term', reserved_4=v4)
			if v5:
				s = s.filter('term', reserved_5=v5)
			if v6:
				s = s.filter('term', reserved_6=v6)
			if has_pic == '0':
				s = s.filter('term', has_pic=False)
			elif has_pic == '1':
				s = s.filter('term', has_pic=True)
			if has_video == '0':
				s = s.filter('term', has_video=False)
			elif has_video == '1':
				s = s.filter('term', has_video=True)
			s = s.filter('range', pdate={'gte': begin, 'lte': to})

			s = s.query('multi_match', query=keyword, fields=scope)
			if not_:
				s = s.exclude('multi_match', query=not_, fields=scope)
			if and_ != None and and_.strip() != '':
				for word in split(r'\s+', and_.strip()):
					s = s.query('multi_match', query=word, fields=scope)
			s = s.highlight('title', fragment_size=50).highlight('content', fragment_size=100).highlight('tag', fragment_size=50).highlight('description', fragment_size=100)
			if f == 'title':
				s = s.exclude('terms', title__raw=l)
			elif f == 'url':
				s = s.exclude('terms', url=l)
			s = s.sort(o+sort_field)
			s = s[from_size:to_size]
			response = s.execute()
			related = related_search(client, keyword)
			return {'success': 1, 'data': response.to_dict(), 'related': related}, 200
		except Exception as e:
			return {'success': 0, 'message': e}, 200

class GdszxSearch(Resource):
	decorators = [check_http_headers, check_request_frequency,]
	def __init__(self):
		super(GdszxSearch, self).__init__()
		self.parser = reqparse.RequestParser()
		self.parser.add_argument('_', type=int, help='时间戳不能空', required=True)
		self.parser.add_argument('appkey', type=str, help='appkey不能空', required=True)
		self.parser.add_argument('token', type=str, help='token不能空', required=True)
		self.parser.add_argument('sign', type=str, help='sign不能空', required=True)
		self.parser.add_argument('page', type=num_limit, default=1)
		self.parser.add_argument('size', type=num_limit, default=10)
		self.parser.add_argument('channel', type=str, help='频道')
		self.parser.add_argument('category', type=str, help='类别')
		self.parser.add_argument('location', type=str, help='地区')
		self.parser.add_argument('times', type=str, help='年代')
		self.parser.add_argument('is_open', type=str, help='是否开放资源')
		self.parser.add_argument('scope', type=str, help='搜索范围', default='')
		self.parser.add_argument('keyword', type=str, required=True, help='关键词')
		self.parser.add_argument('s', type=sort_2_limit, help='排序字段', default='_score')
		self.parser.add_argument('o', type=order_limt, help='排序顺序', default='')
		self.parser.add_argument('and', type=str, help='与关键词')
		self.args = self.parser.parse_args()

	def post(self):
		ts = self.args['_']
		if abs(int(time() * 1000) - int(ts)) > 1800000:
			return {'success':0, 'message': '时间戳无效'}, 200
		token = self.args['token']
		appkey = self.args['appkey']
		verify_token = flask_redis.get(appkey)
		if verify_token is None:
			return {'success': 0, 'message': 'token 无效'}, 200
		else:
			verify_token = verify_token.decode('utf-8') if type(verify_token) == type(b'') else verify_token
			if verify_token != token:
				return {'success': 0, 'message': 'token 无效'}, 200
		sign = self.args['sign']
		if hash_sha256("{0},{1},{2}".format(ts, token, appkey)) != sign:
			return {'success': 0, 'message': 'sign 无效'}, 200
		page = int(self.args['page'])
		size = int(self.args['size'])
		from_size = (page - 1) * size
		to_size = page * size
		channel = self.args['channel']
		category = self.args['category']
		location = self.args['location']
		times = self.args['times']
		and_ = self.args['and']
		sort_field = self.args['s']
		is_open = self.args['is_open']
		o = self.args['o']
		scope = self.args['scope']
		if scope in ['content', 'tag', 'title', 'description', 'author', 'writings']:
			scope = [scope]
		else:
			scope = ['content', 'tag', 'title', 'description', 'author', 'writings']
		keyword = self.args['keyword']
		try:
			s = Search(using=client, index='gdszx', doc_type='culture')
			if times:
				s = s.filter('term', times=times)
			if category:
				s = s.filter('term', category=category)
			if location:
				s = s.filter('term', location=location)
			if channel:
				s = s.filter('term', channel=channel)
			if is_open == '0':
				s = s.filter('term', is_open=False)
			elif is_open == '1':
				s = s.filter('term', is_open=True)
			s = s.query('multi_match', query=keyword, fields=scope)
			if and_ != None and and_.strip() != '':
				for word in split(r'\s+', and_.strip()):
					s = s.query('multi_match', query=word, fields=scope)
			s = s.highlight('title', fragment_size=50).highlight('content', fragment_size=100)
			s.aggs.bucket('times_all', 'terms', field='times', size=10)
			s.aggs.bucket('channel_all', 'terms', field='channel', size=10)
			s.aggs.bucket('category_all', 'terms', field='category', size=10)
			s.aggs.bucket('location_all', 'terms', field='location', size=10)
			s = s.sort(o+sort_field)
			s = s[from_size:to_size]
			response = s.execute()
			return {'success': 1, 'data': response.to_dict()}, 200
		except Exception as e:
			return {'success': 0, 'message': e}, 200