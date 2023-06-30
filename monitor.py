#!/usr/bin/env python3
'''
Created on 30 июн. 2023 г.

@author: demon
'''
from systemd import journal
from datetime import datetime, timedelta
import requests
import time
# import sys
import config

PRIOR = ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"]


def get_chat_id():
    chat_id = ''
    r = requests.get(f'{config.API_SERVER}/getUpdates')
    upd = r.json()
    print(upd)
    if upd['ok']:
        chat_id = upd['result'][0]['message']['from']['id']
    return chat_id


def get_last_entries():
    j = journal.Reader()
    j.add_match(_TRANSPORT='kernel', PRIORITY=PRIOR.index(config.PRIORITY_STR))
    j.seek_realtime(datetime.now() - timedelta(seconds=config.TIMEOUT_SEC))

    to_send = []
    for entry in list(j)[::-1]:
        to_send.append(f"{PRIOR[entry['PRIORITY']].upper()} {entry['__REALTIME_TIMESTAMP']:%H:%M:%S} {entry['SYSLOG_IDENTIFIER']} {entry['_HOSTNAME']}\n>>> {entry['MESSAGE']}")
    text = ''
    for l in to_send:
        if len(text + l) < 4096:
            text += f"{l[::-1]}\n"
        else:
            break
    return text[::-1]


if __name__ == "__main__":
#     get_chat_id()
#     sys.exit()
    while True:
        try:
            text = get_last_entries()
            if text:
                r = requests.post(f"{config.API_SERVER}/sendMessage", params={"chat_id": config.CHAT_ID, "text": text})
                res = r.json()
                if not res['ok']:
                    raise Exception(f"{res['error_code']}: {res['description']}")
        except Exception as e:
            print(e)
        time.sleep(config.TIMEOUT_SEC)

