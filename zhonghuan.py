# -*- encoding: utf-8 -*-

import os
import time
import json

import requests
from lxml import etree

import smtplib
from email.mime.text import MIMEText
from email.header import Header

from config import smtp_server, smtp_username, smtp_password, email_from, email_to, post_id


def log(message: str) -> None:
    print(message)
    time_pre = time.strftime("[%Y-%m-%d %H:%M:%S]: ", time.localtime())
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(time_pre + message + '\n')


def send_email(subject: str, message: str) -> bool:
    mime_message = MIMEText(message, 'plain', 'utf-8')
    mime_message['From'] = Header('物流提醒小助手', 'utf-8')
    mime_message['To'] = Header(email_to, 'utf-8')

    mime_message['Subject'] = Header(subject, 'utf-8')

    try:
        smtp_obj = smtplib.SMTP_SSL(smtp_server)
        smtp_obj.login(smtp_username, smtp_password)
        smtp_obj.sendmail(email_from, email_to, mime_message.as_string())
        log('邮件发送成功')
        return True
    except smtplib.SMTPException:
        log('Error: 无法发送邮件')
        return False


def get_status(post_id_: int, retry_count: int = 5) -> dict:
    source = str()
    while True:
        try:
            source = requests.get(f'http://www.zhonghuanus.com/toDetail.action?parcelNo={post_id_}',
                                  headers={'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8'}).text
            break
        except Exception:
            if retry_count > 0:
                log('Error, retrying...')
                retry_count -= 1
                time.sleep(5)
            else:
                log('Fail requesting.')
                return {'success': False}
            continue

    selector = etree.HTML(source)
    dates = [i.strip() for i in selector.xpath('//ul[@class="status-list"]/li/span[@class="date"]/text()') if i.strip()]
    if not dates:
        log('获取物流信息失败')
        return {'success': False}
    messages = [i.strip() for i in selector.xpath('//ul[@class="status-list"]/li/span[@class="text"]/text()')]
    info = list()
    for i, date in enumerate(dates):
        info.append({'date': date, 'message': messages[i]})

    return {'success': True, 'info': info}


def check_status(post_id_: int) -> None:
    old_info = list()
    if os.path.exists('info.json'):
        with open('info.json', 'r', encoding='utf-8') as file:
            old_info = json.loads(file.read())

    new_status = get_status(post_id_)

    if new_status['success']:
        new_info = new_status['info']
        new_length = len(new_info)
        old_length = len(old_info)

        if new_length > old_length:
            log('有新的物流信息')
            send_email(new_info[0]['date'] + '状态', new_info[0]['message'])
            with open('info.json', 'w', encoding='utf-8') as file:
                file.write(json.dumps(new_info, ensure_ascii=False))
        else:
            log('没有新的物流信息')

    else:
        log('获取新信息失败')


def main() -> None:
    # print(get_status(post_id))
    # send_email('233', '2333')
    check_status(post_id)


if __name__ == '__main__':
    main()
