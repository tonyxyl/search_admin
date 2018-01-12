# coding=utf-8

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError

class SearchForm(FlaskForm):
    keyword = StringField('', validators=[Required()], render_kw={'placeholder': '关键词'})
    submit = SubmitField('搜索')

class FeedForm(FlaskForm):
    email = StringField('您的邮箱', validators=[Required(), Length(5, 64), Email()], render_kw={'placeholder': '留下您的邮箱, 以便我们联系您'})
    content = TextAreaField('反馈内容', validators=[Required(), Length(10, 500)], render_kw={'placeholder': '您的反馈将帮助我们不断提升服务质量'})
    submit = SubmitField('提交')

class BadurlForm(FlaskForm):
    reason = StringField('原因', validators=[Required(), Length(5, 100)], render_kw={'placeholder': '链接存在什么问题'})
    url = TextAreaField('问题链接', validators=[Required(), Length(10, 500)], render_kw={'placeholder': '有问题的链接, 一行一条'})
    submit = SubmitField('提交')