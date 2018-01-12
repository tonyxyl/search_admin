# coding=utf-8

from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response, jsonify
from . import main
from .forms import FeedForm, BadurlForm
from ..models import Feedback, Badurl
from .. import db
from sqlalchemy import or_
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import re
import os

@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('main/index.html')

@main.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedForm()
    if form.validate_on_submit():
        ip = request.headers['X-Real-Ip'] if 'X-Real-Ip' in request.headers else request.remote_addr
        c = Feedback.query.filter(or_(Feedback.ip==ip, Feedback.create_at>datetime.now()-timedelta(minutes=30))).first()
        if c:
            flash('提交太频繁了, 请稍候重试')
        else:
            feedback = Feedback(email=form.email.data, content=form.content.data, ip=ip)
            db.session.add(feedback)
            db.session.commit()
            flash('谢谢您的反馈，我们将在处理后回复您! ')
        return redirect(url_for('main.index'))
    return render_template('main/feedback.html', form=form)

@main.route('/badurl', methods=['GET', 'POST'])
def badurl():
    form = BadurlForm()
    if form.validate_on_submit():
        ip = request.headers['X-Real-Ip'] if 'X-Real-Ip' in request.headers else request.remote_addr
        c = Badurl.query.filter(or_(Badurl.ip==ip, Badurl.create_at>datetime.now()-timedelta(minutes=5))).first()
        if c:
            flash('提交太频繁了, 请稍候重试')
        else:
            badurl = Badurl(reason=form.reason.data, url=form.url.data, ip=ip)
            db.session.add(badurl)
            db.session.commit()
            flash('提交成功, 请耐心等待后台审核')
        return redirect(url_for('main.index'))
    return render_template('main/badurl.html', form=form)