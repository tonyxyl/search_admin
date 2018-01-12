# coding=utf-8

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db, mongo
from ..models import User, Badurl
from sqlalchemy import or_
from .forms import LoginForm, RegistrationForm
from datetime import datetime

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(or_(User.username==form.username.data, User.email==form.username.data)).first()
        if user is not None and user.verify_password(form.password.data):
            if user.confirmed:
                login_user(user, form.remember_me.data)
                last_ip = request.headers['X-Real-Ip'] if 'X-Real-Ip' in request.headers else request.remote_addr
                User.query.filter(User.id==user.id).update({User.last_ip: last_ip, User.last_seen: datetime.utcnow()})
                db.session.commit()
                return redirect(request.args.get('next') or url_for('admin.index'))
            else:
                flash('帐号未通过审核')
        else:
            flash('认证失败')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('退出成功')
    return redirect(url_for('auth.login'))