# 如何使用虚拟环境

Python3.3以上通过venv模块原生支持虚拟环境，命令为`pyvenv`。

##  0. 创建一个名字为`venv`的虚拟环境

`pyvenv venv` 或者 `python3 -m venv /path/to/new/virtual/environment`, 推荐后者

## 1. 激活名字为`venv`的虚拟环境

`source venv/bin/activate`

## 2. 激活虚拟环境命令会修改命令行提示符，显示如下：

`(venv) $`

## 3. 退出当前虚拟环境

`deactivate`

## 4. 安装工具

`pip install gunicorn`

`pip install supervisor` # 只能用python2.7安装

## 5. 在supervisor中配置gunicorn

```
[program:search]
command=/home/venv_search/bin/gunicorn -w 49 -b 127.0.0.1:5050 wsgi:application
directory=/home/tony/search
startsecs=1
stopwaitsecs=1
autostart=true
autorestart=true
startretries=10
stdout_logfile=/var/log/search.stdout.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=2
stderr_logfile=/var/log/search.stderr.log
stderr_logfile_maxbytes=100MB
stderr_logfile_backups=2

[program:nginx]
command=/usr/local/nginx/sbin/nginx
autostart=true
directory=/usr/local/nginx/html
stdout_logfile=/var/log/nginx.stdout.log
redirect_stderr=true
```

## 6. 启动supervisor进程

`supervisord`

## 7. 进入supervisor的控制台

`supervisorctl`

## 8. 在nginx中配置gunicorn反向代理

```
server {
        listen 80;
        server_name  localhost;
        location / {
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Scheme $scheme;
                proxy_redirect off;
                proxy_pass http://127.0.0.1:5050
        }
}

```

<br/>

## 数据库迁移步骤

`python manage.py db init`

`python manage.py db migrate -m "inition migrate"`

`python manage.py db upgrade`

`python manage.py deploy`


## 集成celery

`cd search && celery worker -A celery_runner --loglevel=info`


## mongodb数据同步到elasticserach

`pip install 'mongo-connector[elastic5]'`

`pip install 'elastic2-doc-manager[elastic5]'`

**配置supervisor**

```
[program:mongod]
command=mongod -f /etc/mongod.conf --replSet mySet
directory=/home
autostart=true
autorestart=true

[program:mongo-connector]
command=mongo-connector -m 127.0.0.1:27017 -t 127.0.0.1:9200 -d elastic2_doc_manager
directory=/home
autostart=true
autorestart=true
```

**flask_bootstrap使用本地或其他cdn资源**

- 加载本地资源, 只需传入相关配置

```
app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
```

- 使用其他cdn资源, 找到`~/venv/lib/site-packages/flask_bootstrap/__init__.py`文件并修改如下

```
bootstrap = lwrap(
    WebCDN('//cdn.bootcss.com/bootstrap/%s/' % BOOTSTRAP_VERSION), local)

jquery = lwrap(
    WebCDN('//cdn.bootcss.com/jquery/%s/' % JQUERY_VERSION), local)

html5shiv = lwrap(
    WebCDN('//cdn.bootcss.com/html5shiv/%s/' % HTML5SHIV_VERSION))

respondjs = lwrap(
    WebCDN('//cdn.bootcss.com/respond.js/%s/' % RESPONDJS_VERSION))
```

`flask_moment`使用其他cdn需要找到`~/venv/lib/site-packages/flask_moment.py`修改.
