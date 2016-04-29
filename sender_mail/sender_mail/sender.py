#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
- 有独立的线程定时发送告警, 保证单位时间内不会有太多的告警骚扰到用户
- 被收敛的告警，在时间到了之后会自动合并，一次发送给用户
'''
import logging
import threading
import time
import mymail
from datetime import datetime, timedelta 

mutex = threading.Lock()
tobe_send = []
max_queue = 10
warning_send_thread = None
sender_config = {}

class WarningSendThread(threading.Thread):
    def __init__(self, cfg):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("warning send thread")
        self.min_warning_send_interval = cfg.get("min_warning_send_interval", 60)
        self.cfg = cfg

    def run(self):
        logging.info("warning send thread runing")
        while True:
            try:
                last_warning_send_at = sender_config.get('last_warning_send_at', datetime.min)
                logging.debug("warning send thread:%s %s", last_warning_send_at, datetime.now())
                if datetime.now() - last_warning_send_at < timedelta(seconds=self.min_warning_send_interval):
                    continue

                # 复制一份后清空
                mutex.acquire()
                warnings = tobe_send[:]
                tobe_send[:] = []
                mutex.release()

                _send(warnings, self.cfg)
            except:
                logging.exception("warning send thread error")
            finally:
                time.sleep(1)


def init(cfg):
    warning_send_thread = WarningSendThread(cfg)
    warning_send_thread.start()


def _send(warnings,cfg):
    if len(warnings) < 1:
        return
    sender_config['last_warning_send_at'] = datetime.now()
    for rule, ret in warnings:
        rule['keep_fail_count'] = 0
        logging.info("send warning:%s", warnings)
        mymail.send(warnings,cfg["senders"])


def _sendwarnings(rule, ret, cfg):
    last_warning_send_at = sender_config.get('last_warning_send_at', datetime.min)
    min_warning_send_interval = cfg.get("min_warning_send_interval", 60)
    logging.info("sendwarnings recive:%s %s", rule, ret)

    if datetime.now() - last_warning_send_at < timedelta(min_warning_send_interval):
        mutex.acquire()
        if len(tobe_send) < max_queue:
            tobe_send.append((rule, ret))
        else:
            logging.info("sendwarnings queue full:%s %s", rule, ret)
        mutex.release()
    else:
        _send([(rule, ret)], cfg)

def task_fail(rule, ret, cfg):
    fail_count = rule.get('fail_count', 0)
    rule['fail_count'] = fail_count + 1

    max_keep_fail_count = rule.get('max_keep_fail_count', cfg.get('max_keep_fail_count', 3))
    keep_fail_count = rule.get('keep_fail_count', 0)
    rule['keep_fail_count'] = keep_fail_count + 1
    if keep_fail_count >= max_keep_fail_count:
        _sendwarnings(rule, ret, cfg)
    logging.debug('task_fail:%s', rule)

def task_success(rule, cfg):
    success_count = rule.get('success_count', 0)
    rule['success_count'] = success_count + 1
    rule['keep_fail_count'] = 0
    logging.debug('task_success:%s', rule)

if __name__ == "__main__":
    cfg = {
            # 单个监控任务连续几次失败后产生告警 
            "max_keep_fail_count": 1,
            # 两次告警之间的最小间隔，单位是秒，用户防止告警骚扰
            "min_warning_send_interval": 6,
            "senders": 
                {
                    "smtp_server": "smtp.163.com",
                    "smtp_user": "XXXXXXXXX",
                    "smtp_pass": "XXXXXXXXX",
                    "mail_postfix":"163.com",
                    "from": "XXXXXXXXX@163.com", 
                    "to": ["XXXXXXXXX@qq.com"]
                }
                
        }
    init(cfg)
    rule={
                'fail_count': 0, 
                u'args': {
                    u'title': u'service have a error',
                    u'target': u'http://www.baidu.com'
                }, 
                u'type': u'curl', 
                'id': 1, 
                'keep_fail_count': 0
            }
    ret='12222'
    while True:
        task_fail(rule, ret, cfg)
        time.sleep(1)

