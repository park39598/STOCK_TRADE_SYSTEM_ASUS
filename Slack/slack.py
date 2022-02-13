from slacker import Slacker
import asyncio
import websockets
from slackclient import SlackClient
import time



class Slack():
    def __init__(self):
        self.token = '2111552958:AAFcTY2nJIGt1EWeJ2klZ9m-mjVM5dU0b2g'
        self.loop = asyncio.new_event_loop()
        self.slack = Slacker(self.token)
        self.sc = SlackClient(self.token)
        asyncio.set_event_loop(self.loop)
        asyncio.get_event_loop().run_until_complete(self.execute_bot())
        asyncio.get_event_loop().run_forever()

    def notification(self, pretext=None, title=None, fallback=None, text=None):
        attachments_dict = dict()
        attachments_dict['pretext'] = pretext  # test1
        attachments_dict['title'] = title  # test2
        attachments_dict['fallback'] = fallback  # test3
        attachments_dict['text'] = text  # test4
        attachments = [attachments_dict]
        self.slack.chat.post_message(channel='﻿#﻿stock_trading_machine', text=None, attachments=attachments,
                                     as_user=None)

    def execute_bot(self):
        if self.sc.rtm_connect():
            while True:
                res = self.sc.rtm_read()
                if len(res):
                    keys = list(res[0].keys())
                    if 'type' in keys and 'text' in keys and 'user' in keys:
                        print(res[0])
                        message = res[0]['text']
                        self.notification(message + ' mung')
                time.sleep(1)
        else:
            print('connection fail')



if __name__ == "__main__":
    slk = Slack()
    slk.notification('sa', 'a', 'a', 'f')
