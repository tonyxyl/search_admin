# coding=utf-8

from flask_admin.contrib.sqla import ModelView
from flask_admin.form import rules, SecureForm
from flask_admin import BaseView, expose, babel, actions
from flask_login import login_required, current_user
from wtforms.fields import StringField, PasswordField
from wtforms.validators import Email, Required, Length, Regexp
from werkzeug.security import generate_password_hash
from flask import redirect, url_for


class MyIndexView(BaseView):
    def __init__(self, name=None, category=None, endpoint=None, url=None, template='manage/index.html', menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
        super(MyIndexView, self).__init__(name or babel.lazy_gettext('后台'),
            category,
            endpoint or 'admin',
            '/admin' if url is None else url,
            'static',
            menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type,
            menu_icon_value=menu_icon_value)
        self._template = template

    @login_required
    @expose()
    def index(self):
        return self.render(self._template)

class ModelMixin(object):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role_id == 1

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

    def is_visible(self):
        return True

class UserView(ModelMixin, ModelView):
    can_create = True
    can_edit = True
    can_delete = True
    column_labels = dict(email='邮箱', username='用户名', realname='备注', confirmed='是否启用', last_ip='登录ip')
    column_exclude_list = ('password_hash', 'last_seen', 'member_since')
    #form_columns = ('username', 'realname', 'email', 'last_ip', 'confirmed', 'last_ip')
    form_excluded_columns = ('password_hash', 'last_seen', 'member_since', 'last_ip')
    #form_edit_rules = ('email', 'password_hash', 'realname')
    #form_overrides = dict(password_hash=PasswordField)
    column_filters=('username', 'email', 'realname')
    column_searchable_list = ('username', 'email', 'realname')
    form_args = dict(
        email=dict(label='邮箱', validators=[Email()])
    )

    def __init__(self, session, **kwargs):
        from ..models import User
        super(UserView, self).__init__(User, session, **kwargs)

    def on_model_change(self, form, model, is_created):
        if len(model.password_hash) > 0:
            model.password_hash = generate_password_hash(model.password_hash)

    def scaffold_form(self):
        form_class = super(UserView, self).scaffold_form()
        form_class.password_hash = PasswordField('密码')
        return form_class

class RoleView(ModelMixin, ModelView):
    column_labels = dict(name='名字', desc='说明', permissions='权限',)
    form_columns = ('name', 'desc', 'permissions')
    column_exclude_list = ('permissions',)
    form_create_rules = ('name', rules.Text('在两个field直接添加文字'), 'desc', 'permissions')

    def __init__(self, session, **kwargs):
        from ..models import Role
        super(RoleView, self).__init__(Role, session, **kwargs)

class RightView(ModelMixin, ModelView):
    column_labels = dict(info='权限说明', route='路由',)

    def __init__(self, session, **kwargs):
        from ..models import Permission
        super(RightView, self).__init__(Permission, session, **kwargs)

class WebsiteView(ModelMixin, ModelView):
    can_create = True
    can_edit = True
    can_delete = True
    column_labels = dict(name='网站名称', domain='网站域名')
    form_columns = ('name', 'domain')

    def __init__(self, session, **kwargs):
        from ..models import Website
        super(WebsiteView, self).__init__(Website, session, **kwargs)

class ChannelView(ModelMixin, ModelView):
    can_create = True
    can_edit = False
    can_delete = False
    column_labels = dict(name='栏目名')

    def __init__(self, session, **kwargs):
        from ..models import Channel
        super(ChannelView, self).__init__(Channel, session, **kwargs)

class HotwordView(ModelMixin, ModelView):
    column_labels = dict(keyword='热词', inuse='是否启用', since='添加日期')

    def __init__(self, session, **kwargs):
        from ..models import Hotword
        super(HotwordView, self).__init__(Hotword, session, **kwargs)

class SensitiveView(ModelMixin, ModelView):
    column_labels = dict(keyword='敏感词', inuse='是否启用', since='添加日期')

    def __init__(self, session, **kwargs):
        from ..models import Sensitive
        super(SensitiveView, self).__init__(Sensitive, session, **kwargs)

class TokenView(ModelMixin, ModelView):
    column_labels = dict(info='说明', create_at='添加日期')

    def __init__(self, session, **kwargs):
        from ..models import Token
        super(TokenView, self).__init__(Token, session, **kwargs)

class FeedbackView(ModelMixin, ModelView):
    column_labels = dict(email='用户邮箱', create_at='添加日期', content='留言内容', checked='已处理')

    def __init__(self, session, **kwargs):
        from ..models import Feedback
        super(FeedbackView, self).__init__(Feedback, session, **kwargs)

class BadurlView(ModelMixin, ModelView):
    column_labels = dict(url='链接', create_at='添加日期', reason='原因', checked='已处理')

    def __init__(self, session, **kwargs):
        from ..models import Badurl
        super(BadurlView, self).__init__(Badurl, session, **kwargs)