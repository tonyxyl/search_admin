# coding=utf-8
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_moment import Moment
from config import config
from flask_admin import Admin
from flask_babelex import Babel
from flask_restful import Api
from flask_cors import CORS
from flask_redis import FlaskRedis
from flask_pymongo import PyMongo
from flask_celery import Celery
import warnings
from app.manage import *

bootstrap = Bootstrap()
mail = Mail()
db = SQLAlchemy()
moment = Moment()
pagedown = PageDown()
flask_redis = FlaskRedis()
mongo = PyMongo()
flask_celery = Celery()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录再访问'
login_manager.login_message_category = 'info'

babel = Babel()
admin = Admin(name='搜索后台', index_view=MyIndexView(), base_template='manage/my_base.html')

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', 'Fields missing from ruleset', UserWarning)
    admin.add_view(UserView(db.session, name='用户管理', category='RBAC'))
    admin.add_view(RoleView(db.session, name='角色管理', category='RBAC'))
    admin.add_view(RightView(db.session, name='权限管理', category='RBAC'))
    admin.add_view(WebsiteView(db.session, name='网站管理', category='搜索管理'))
    admin.add_view(ChannelView(db.session, name='栏目管理', category='搜索管理'))
    admin.add_view(HotwordView(db.session, name='热词管理', category='搜索管理'))
    admin.add_view(SensitiveView(db.session, name='敏感词管理', category='搜索管理'))
    admin.add_view(FeedbackView(db.session, name='用户反馈', category='搜索管理'))
    admin.add_view(BadurlView(db.session, name='问题链接', category='搜索管理'))
    admin.add_view(TokenView(db.session, name='授权管理', category='搜索管理'))

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    CORS(app, supports_credentials=True)
    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    pagedown.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    api = Api(app)
    admin.init_app(app)
    flask_redis.init_app(app)
    mongo.init_app(app)
    flask_celery.init(app)
    #event.listen(Reminder, 'after_insert', on_reminder_save)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.api_v1 import TokenApi, SearchApi, SuggestApi, GdszxSearch
    api.add_resource(TokenApi, '/api/v1/token')
    api.add_resource(SearchApi, '/api/v1/search')
    api.add_resource(SuggestApi, '/api/v1/suggest')
    api.add_resource(GdszxSearch, '/api/v1/gdszxsearch')

    return app