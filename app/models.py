# coding=utf-8

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from flask import current_app, request, url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

class Permission(db.Model):
    __tablename__ = 'rights'
    id = db.Column(db.Integer, primary_key=True)
    info = db.Column(db.String(32), nullable=False)
    route = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return '<Permission %r>' % self.__tablename__

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    desc = db.Column(db.String(128), nullable=False)
    permissions = db.Column(db.Text, nullable=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        role = Role.query.filter_by(id = 1).first()
        if role is None:
            role = Role(name='超级管理员', desc='所有权限', permissions='')
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), index=True, unique=True, nullable=False)
    username = db.Column(db.String(32), unique=True, index=True, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    realname = db.Column(db.String(32), nullable=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    last_ip = db.Column(db.String(32), default='127.0.0.1')

    @property
    def password(self):
        raise AttributeError('密码不可读')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        user = User.query.get(data['id'])
        return user

    @staticmethod
    def insert_users():
        user_data = {}
        user = User.query.filter_by(username = 'admin').first()
        if user is None:
            user = User(email='admin@admin.com', username='adminAdmin', role_id=1, password_hash=generate_password_hash('yourpassword'), confirmed=1, realname='管理员')
            db.session.add(user)
        db.session.commit()

    def __repr__(self):
        return '<User %r>' % self.username

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Hotword(db.Model):
    __tablename__ = 'hotwords'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(128), unique=True, index=True, nullable=False)
    inuse = db.Column(db.Boolean, default=True)
    since = db.Column(db.DateTime(), default=datetime.utcnow)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False,  default=1)

    def __repr__(self):
        return '<Hotword %r>' % self.keyword

class Sensitive(db.Model):
    __tablename__ = 'sensitive'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(128), unique=True, index=True, nullable=False)
    inuse = db.Column(db.Boolean, default=True)
    since = db.Column(db.DateTime(), default=datetime.utcnow)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False, default=1)

    def __repr__(self):
        return '<Sensitive %r>' % self.keyword

class Website(db.Model):
    __tablename__ = 'websites'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    domain = db.Column(db.String(128), unique=True, index=True, nullable=False)
    hotwords = db.relationship('Hotword', backref='website', lazy='dynamic')
    channels = db.relationship('Channel', backref='website', lazy='dynamic')
    sensitives = db.relationship('Sensitive', backref='website', lazy='dynamic')
    tokens = db.relationship('Token', backref='website', lazy='dynamic')

    def __repr__(self):
        return '<Website %r>' % self.name

class Channel(db.Model):
    __tablename__ = 'channels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, index=True, nullable=False)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False,  default=1)

    def __repr__(self):
        return '<Channel %r>' % self.name

class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    request_url = db.Column(db.Text, nullable=False)
    keyword = db.Column(db.String(128), nullable=True)
    date = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return '<History %r>' % self.keyword

class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, primary_key=True)
    info = db.Column(db.String(128), index=True, unique=True, nullable=False)
    appkey = db.Column(db.String(32), unique=True, nullable=False)
    appsecret = db.Column(db.String(128), nullable=False)
    frequent = db.Column(db.Integer, nullable=False)
    create_at = db.Column(db.DateTime(), default=datetime.utcnow)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False,  default=1)

    def __repr__(self):
        return '<Token %r>' % self.info

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    create_at = db.Column(db.DateTime(), default=datetime.utcnow)
    ip = db.Column(db.String(40), nullable=True)
    checked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Feedback %r>' % self.__tablename__

class Badurl(db.Model):
    __tablename__ = 'badurl'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(200), nullable=False, unique=True)
    reason = db.Column(db.String(100), nullable=False)
    checked = db.Column(db.Boolean, default=False)
    create_at = db.Column(db.DateTime(), default=datetime.utcnow)
    ip = db.Column(db.String(40), nullable=True)

    def __repr__(self):
        return '<Badurl %r>' % self.__tablename__

class Reminder(db.Model):
    __tablename__ = 'reminders'
    id = db.Column(db.String(45), primary_key=True)
    date = db.Column(db.DateTime())
    email = db.Column(db.String(255))
    text = db.Column(db.Text())

    def __init__(self, id, text):
        self.id = id
        self.email = text

    def __repr__(self):
        return '<Model Reminder `{}`>'.format(self.text[:20])