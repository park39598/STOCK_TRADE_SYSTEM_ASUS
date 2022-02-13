from slacker import Slacker
import asyncio
import websockets
#
class Slack():
    def __init__(self):
        self.token = 'xoxp-1367148855493-1394081137760-1394430733136-fc8e5068c173634ee916f352d13efbb3'
        self.loop = asyncio.new_event_loop()
        self.slack = Slacker(self.token)
        asyncio.set_event_loop(self.loop)
        asyncio.get_event_loop().run_until_complete(self.execute_bot())
        asyncio.get_event_loop().run_forever()

    def notification(self, pretext=None, title=None, fallback=None, text=None):
        attachments_dict = dict()
        attachments_dict['pretext'] = pretext #test1
        attachments_dict['title'] = title #test2
        attachments_dict['fallback'] = fallback #test3
        attachments_dict['text'] = text #test4
        attachments = [attachments_dict]
        self.slack.chat.post_message(channel='﻿#﻿stockautotrade', text=None, attachments=attachments, as_user=None)

    async def execute_bot(self):
        res = self.slack.rtm.connect()
        endpoint = res.body['url']
        ws = await websockets.connect(endpoint)
        while True:
            message_json = await ws.recv()
            print(message_json)



if __name__ == "__main__":
    slk = Slack()
    slk.notification('sa','a','a','f')

