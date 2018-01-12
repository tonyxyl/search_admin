# coding=utf-8

import stmplib
import datetime
from . import mail, flask_celery
from flask_mail import Message
from email.mime.text import MIMEText
from .models import Reminder

@flask_celery.task(bind=True, ignore_result=True, default_retry_delay=300, max_retries=5)
def remind(self, primary_key):
    """
    send remind email to user when registered
    """
    reminder = Reminder.query.get(primary_key)

    msg = MIMEText(reminder.text)
    msg['Subject'] = 'Welcome!'
    msg['From'] = 'admin@admin.com'
    msg['To'] = reminder.email

    try:
        smtp_server = smtplib.SMTP('')
        smtp_server.starttls()
        smtp_server.login('user', 'pass')
        smtp_server.sendmail('admin@admin.com', [reminder.email], msg.as_string())
        smtp_server.close()
        return
    except Exception as err:
        self.retry(exc=err)

def on_reminder_save(mapper, connect, self):
    remind.apply_async(args=(self.id), eta=self.date)