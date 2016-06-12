#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email.header import Header
import json

def _get_mail_content(warnings):
    content = ''
    for rule, ret in warnings:
        content += u'## 告警内容：\n%s \n\n' % rule['args'].get("title")
        content += u'## 告警结果：\n%s \n\n' % str(ret)
        content += u'## 告警规则：\n%s \n\n' % json.dumps(rule, indent=4)
        content += u'====================\n\n' 
    return content


def send(warnings,senders):
    logging.info("mail send:%s", warnings)
    content = _get_mail_content(warnings)
    print content
    return
    
    rule = warnings[0][0]  # 取第一个告警的rule
    title = rule['args'].get("title", u"监控告警")
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = Header(u'监控告警：%s' % title, 'utf-8')
    msg["From"] = senders["from"]
    msg['To'] = senders["to"][0]
    msg['Date'] = formatdate(localtime=True)
    try:
        server = smtplib.SMTP()
        server.connect(senders["smtp_server"])
        server.login(senders["smtp_user"], senders["smtp_pass"])
        address=senders["smtp_user"]+'<'+senders["smtp_user"]+'@'+senders["mail_postfix"]+'>'
        server.sendmail(address,senders["to"][0], msg.as_string())
        server.close()
    except Exception:
        logging.exception('sender.mail send error:%s', warnings)

if __name__ == '__main__':
    senders={
                 "smtp_server": "smtp.163.com",
                 "smtp_user": "XXXXXXXXX",
                 "smtp_pass": "XXXXXXXXX",
                 "mail_postfix":"163.com",
                 "from": "XXXXXXXXX@163.com", 
                 "to": ["XXXXXXXXX@qq.com"]
            }
    bin=[
        (
            {
                'fail_count': 2, 
                u'args': {
                    u'title': u'service have a error',
                    u'target': u'http://www.baidu.com'
                }, 
                u'type': u'curl', 
                'id': 1, 
                'keep_fail_count': 0
            }, 
            'execute timeout'
        )
    ]
    send(bin,senders)
