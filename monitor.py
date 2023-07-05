#!/usr/bin/env python3
'''
Created on 30 июн. 2023 г.

@author: demon
'''
from pathlib import Path
from systemd import journal
from datetime import datetime, timedelta
import requests
import time
import argparse
# import sys
import config

PRIOR = ["emerg", "alert", "crit", "err", "warning", "notice", "info", "debug"]


def createParser():
    parser = argparse.ArgumentParser(description="Monitor journal and send messages to telegram bot",
                                     epilog='(c) 2023 Dmitriy Vorotilin',
                                     prog=Path(__file__).name)
    parser.add_argument('--priority', '-p', help='Priority of messages', default=config.PRIORITY_STR)
    parser.add_argument('--timeout', '-t', type=int, help='Timeout in seconds of checks of journal', default=config.TIMEOUT_SEC)
    parser.add_argument('--message', '-m', help='Send custom message to bot')

    return parser


class journalMonitor():

    def __init__(self):
        self.options = createParser().parse_args()

    def get_chat_id(self):
        chat_id = ''
        r = requests.get(f'{config.API_SERVER}/getUpdates')
        upd = r.json()
        print(upd)
        if upd['ok']:
            chat_id = upd['result'][0]['message']['from']['id']
        return chat_id

    def sendMessage(self, text):
        if text:
            r = requests.post(f"{config.API_SERVER}/sendMessage", params={"chat_id": config.CHAT_ID, "text": text[-4096:]})
            res = r.json()
            if not res['ok']:
                raise Exception(f"{res['error_code']}: {res['description']}")

    def get_last_entries(self):
        j = journal.Reader()
        j.add_match(_TRANSPORT='kernel')
        j.add_match(_TRANSPORT='syslog')
        j.add_match(PRIORITY=PRIOR.index(self.options.priority))
        j.seek_realtime(datetime.now() - timedelta(seconds=self.options.timeout))

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

    def daemon(self):
        while True:
            try:
                self.sendMessage(self.get_last_entries())
            except Exception as e:
                print(e)
            time.sleep(self.options.timeout)
        else:
            self.sendMessage(self.get_last_entries())


if __name__ == "__main__":
    jm = journalMonitor()
#     jm.get_chat_id()
#     sys.exit()
    if jm.options.message:
        jm.sendMessage(jm.options.message)
    else:
        jm.daemon()

