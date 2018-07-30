import unittest
from unittest.mock import patch, Mock
import json
import asyncio
from asyncio import coroutine
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

# from translationbot import main as translation
from telegrambot.translationbot import main as translation

with open('../config.json', 'r') as f:
    config = json.load(f)
TOKEN = config['telegram']['test']
SERVER = 'http://langChainext-5c6a881e9c24431b.elb.ap-northeast-1.amazonaws.com:5000'

def CoroMock():
    coro = Mock(name="CoroutineResult")
    corofunc = Mock(name="CoroutineFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    corofunc.coro.return_value = True
    return corofunc

def CoroMockReadUpdateId():
    coro = Mock(name="GetUpdateIdResult")
    corofunc = Mock(name="GetUpdateIdFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    corofunc.coro.return_value = 20180727
    return corofunc

def CoroMockSendReplyMessage():
    coro = Mock(name="GetUpdateIdResult")
    corofunc = Mock(name="GetUpdateIdFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    corofunc.coro.return_value = {
        'ok': True,
        'result': {
            'chat': {
                'first_name': 'SunHo',
                'id': 604252092,
                'last_name': 'Lee',
                'type': 'private',
                'username': 'ooohnus'
            },
            'date': 1532421908,
            'entities': [
                {'length': 14, 'offset': 0, 'type': 'italic'},
                {'length': 31, 'offset': 80, 'type': 'bold'},
                {'length': 15, 'offset': 237, 'type': 'italic'},
                {'length': 20, 'offset': 296, 'type': 'italic'}
            ],
            'from': {
                'first_name': 'sunnytestbot',
                'id': 561471433,
                'is_bot': True,
                'username': 'sunnytestbot'
            },
            'message_id': 1119,
            'reply_to_message': {
                'chat': {
                    'first_name': 'SunHo',
                    'id': 604252092,
                    'last_name': 'Lee',
                    'type': 'private',
                    'username': 'ooohnus'
                },
                'date': 1532421561,
                'from': {
                    'first_name': 'SunHo',
                    'id': 604252092,
                    'is_bot': False,
                    'language_code': 'ko-KR',
                    'last_name': 'Lee',
                    'username': 'ooohnus'
                },
                'message_id': 1114,
                'text': "!enko It's such a beautiful day"
            },
            'text': 'Translating...'
        }
    }
    return corofunc

def CoroMocGetUpdates():
    coro = Mock(name="GetUpdatesResult")
    corofunc = Mock(name="GetUpdatesFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    corofunc.coro.return_value = [
        {
            "update_id": 524784346,
            "message": {
                "message_id": 1482,
                "from": {
                    "id": 604252092,
                    "is_bot": False,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "language_code": "ko-KR"
                },
                "chat": {
                    "id": 604252092,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "type": "private"
                },
                "date": 1532666246,
                "text": "/start",
                "entities": [
                    {
                        "offset": 0,
                        "length": 6,
                        "type": "bot_command"
                    }
                ]
            }
        },
        {
            "update_id": 524784347,
            "message": {
                "message_id": 1483,
                "from": {
                    "id": 604252092,
                    "is_bot": False,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "language_code": "ko-KR"
                },
                "chat": {
                    "id": 604252092,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "type": "private"
                },
                "date": 1532666257,
                "text": "!enko It's such a beautiful day"
            }
        },
        {
            "update_id": 524784348,
            "message": {
                "message_id": 1484,
                "from": {
                    "id": 604252092,
                    "is_bot": False,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "language_code": "ko-KR"
                },
                "chat": {
                    "id": 604252092,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "type": "private"
                },
                "date": 1532666271,
                "text": "!enkr It's such a beautiful day"
            }
        },
        {
            "update_id": 524784349,
            "message": {
                "message_id": 1485,
                "from": {
                    "id": 604252092,
                    "is_bot": False,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "language_code": "ko-KR"
                },
                "chat": {
                    "id": 604252092,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "type": "private"
                },
                "date": 1532666278,
                "text": "!enko"
            }
        }
    ]
    return corofunc

class TrainerTestCase(unittest.TestCase):
    @patch('telegrambot.translationbot.TOKEN', return_value=TOKEN)
    @patch('telegrambot.translationbot.TranslationBot.write_last_update_id', new_callable=CoroMock)
    @patch('telegrambot.translationbot.TranslationBot.read_last_update_id', new_callable=CoroMockReadUpdateId)
    @patch('telegrambot.translationbot.TranslationBot.get_updates', new_callable=CoroMocGetUpdates)
    @patch('telegrambot.translationbot.TranslationBot.send_message', new_callable=CoroMock)
    @patch('telegrambot.translationbot.TranslationBot.send_message_with_data', new_callable=CoroMock)
    @patch('telegrambot.translationbot.TranslationBot.send_reply_message', new_callable=CoroMockSendReplyMessage)
    @patch('telegrambot.translationbot.TranslationBot.edit_message', new_callable=CoroMock)
    @patch('telegrambot.translationbot.TranslationBot.answer_callback_query', new_callable=CoroMock)
    def test_msg_handling(self, t, w, r, g, s1, s2, s3, e, a):
        actions = ['New user', 'Translate']
        loop = asyncio.get_event_loop()
        ret = loop.run_until_complete(translation())
        # self.assertTrue(ret)
        self.assertEqual(ret, 524784350)

if __name__ == '__main__':
    unittest.main()
