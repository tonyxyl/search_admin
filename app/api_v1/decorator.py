# coding=utf-8

from functools import wraps
from flask import request, jsonify
from re import search
from time import time, localtime, strftime
from .. import flask_redis

def http_headers(user_agent, referer):
    if search(r'(Windows NT|Mac OS X|Linux|iPhone|Android)', user_agent) != None and search(r'(.com|.cn)', referer) != None:
        return True
    return False

def check_http_headers(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        headers = request.headers
        referer = headers['Referer'] if 'Referer' in headers else ''
        user_agent = headers['User-Agent'] if 'User-Agent' in headers else ''
        if http_headers(user_agent, referer) == False:
            return jsonify({'success': 0, 'mesage': ':D'})
        return func(*args, **kwargs)
    return decorated

def check_timestamp(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        args = request.args
        if '_'  not in args:
            return jsonify({'success': 0, 'message': '时间戳无效'})
        else:
            ts = args['_']
            if ts.isdigit() == False:
                return jsonify({'success': 0, 'message': '时间戳必须是整数'})
        if abs(int(time() * 1000) - int(ts)) > 10000:
            return jsonify({'success': 0, 'message': '时间戳无效'})
        return func(*args, **kwargs)
    return decorated

def request_frequency(ip, limit):
    if flask_redis.exists(ip):
        return False
    ts = strftime('%Y%m%d%H%M', localtime())
    key = '{0}:{1}'.format(ip, ts)
    d = flask_redis.get(key)
    if d is not None and int(d) > limit:
        flask_redis.setex(ip, 300, 'blocked')
        return False
    else:
        pipe = flask_redis.pipeline(transaction=True)
        flask_redis.incr(key, 1)
        flask_redis.expire(key, 60)
        pipe.execute()
    return True

def check_request_frequency(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        headers = request.headers
        ip = headers['X-Real-Ip'] if 'X-Real-Ip' in headers else request.remote_addr
        if request_frequency(ip, 40) == False:
            return jsonify({'success': 0, 'message': '请求太频繁, 请5分钟后尝试'})
        return func(*args, **kwargs)
    return decorated