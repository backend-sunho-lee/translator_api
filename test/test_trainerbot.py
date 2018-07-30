import unittest
from unittest.mock import patch, Mock
import json
import asyncio
from asyncio import coroutine
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

# from trainerbot import main as trainer
from telegrambot.trainerbot import main as trainer

with open('../config.json', 'r') as f:
    config = json.load(f)
TOKEN = config['telegram']['test']

def CoroMock():
    coro = Mock(name="CoroutineResult")
    corofunc = Mock(name="CoroutineFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    corofunc.coro.return_value = True
    return corofunc

def CoroMockReadUpdateId():
    coro = Mock(name="CoroutineResult")
    corofunc = Mock(name="CoroutineFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    corofunc.coro.return_value = 201807271342
    return corofunc

def CoroMocGetUpdates():
    coro = Mock(name="CoroutineResult")
    corofunc = Mock(name="CoroutineFunction", side_effect=coroutine(coro))
    corofunc.coro = coro
    corofunc.coro.return_value = [
    {
        "update_id": 524784315,
        "message": {
            "message_id": 1371,
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
            "date": 1532590620,
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
        "update_id": 524784316,
        "message": {
            "message_id": 1372,
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
            "date": 1532590636,
            "text": "💰My point"
        }
    },
    {
        "update_id": 524784317,
        "message": {
            "message_id": 1373,
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
            "date": 1532590638,
            "text": "✏️Translate"
        }
    },
    {
        "update_id": 524784318,
        "message": {
            "message_id": 1374,
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
            "date": 1532590641,
            "text": "⚙Set Language"
        }
    },
    {
        "update_id": 524784319,
        "callback_query": {
            "id": "2595242976141204979",
            "from": {
                "id": 604252092,
                "is_bot": False,
                "first_name": "SunHo",
                "last_name": "Lee",
                "username": "ooohnus",
                "language_code": "ko-KR"
            },
            "message": {
                "message_id": 1339,
                "from": {
                    "id": 561471433,
                    "is_bot": True,
                    "first_name": "sunnytestbot",
                    "username": "sunnytestbot"
                },
                "chat": {
                    "id": 604252092,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "type": "private"
                },
                "date": 1532587477,
                "text": "Cool! You chose en!\nThen, please choose one language that you want to translate to!",
                "entities": [
                    {
                        "offset": 16,
                        "length": 2,
                        "type": "bold"
                    },
                    {
                        "offset": 80,
                        "length": 2,
                        "type": "bold"
                    }
                ]
            },
            "chat_instance": "8524903154770542179",
            "data": "2nd|ko"
        }
    },
        {
            "update_id": 524784328,
            "message": {
                "message_id": 1390,
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
                "date": 1532596355,
                "text": "행복합시다"
            }
        },
        {
            "update_id": 524784329,
            "callback_query": {
                "id": "2595242975432779955",
                "from": {
                    "id": 604252092,
                    "is_bot": False,
                    "first_name": "SunHo",
                    "last_name": "Lee",
                    "username": "ooohnus",
                    "language_code": "ko-KR"
                },
                "message": {
                    "message_id": 1377,
                    "from": {
                        "id": 561471433,
                        "is_bot": True,
                        "first_name": "sunnytestbot",
                        "username": "sunnytestbot"
                    },
                    "chat": {
                        "id": 604252092,
                        "first_name": "SunHo",
                        "last_name": "Lee",
                        "username": "ooohnus",
                        "type": "private"
                    },
                    "date": 1532590815,
                    "text": "Current setting: en → ko\n\nWhich language do you want to translate from?",
                    "entities": [
                        {
                            "offset": 0,
                            "length": 24,
                            "type": "bold"
                        },
                        {
                            "offset": 66,
                            "length": 4,
                            "type": "bold"
                        }
                    ]
                },
                "chat_instance": "8524903154770542179",
                "data": "1st|ko"
            }
        },
        {
            "update_id": 524784330,
            "message": {
                "message_id": 1391,
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
                "date": 1532596537,
                "document": {
                    "file_name": "home_oh1.jpg",
                    "mime_type": "image/jpeg",
                    "thumb": {
                        "file_id": "AAQFABMgztYyAAQLVwaekI9o1oNGAAIC",
                        "file_size": 3957,
                        "width": 66,
                        "height": 90
                    },
                    "file_id": "BQADBQADQAADH7rQVowkxSsmXnsjAg",
                    "file_size": 37291
                }
            }
        }
    ]
    return corofunc

class TrainerTestCase(unittest.TestCase):
    @patch('telegrambot.trainerbot.TOKEN', return_value=TOKEN)
    @patch('telegrambot.trainerbot.TrainerBot.write_last_update_id', new_callable=CoroMock)
    @patch('telegrambot.trainerbot.TrainerBot.read_last_update_id', new_callable=CoroMockReadUpdateId)
    @patch('telegrambot.trainerbot.TrainerBot.get_updates', new_callable=CoroMocGetUpdates)
    @patch('telegrambot.trainerbot.TrainerBot.send_message', new_callable=CoroMock)
    @patch('telegrambot.trainerbot.TrainerBot.send_message_with_data', new_callable=CoroMock)
    @patch('telegrambot.trainerbot.TrainerBot.send_reply_message', new_callable=CoroMock)
    @patch('telegrambot.trainerbot.TrainerBot.edit_message', new_callable=CoroMock)
    @patch('telegrambot.trainerbot.TrainerBot.answer_callback_query', new_callable=CoroMock)
    def test_msg_handling(self, t, w, r, g, s1, s2, s3, e, a):
        actions = ['Multimedia Error', 'New user', 'Balance check', 'Get sentence', 'Set language', 'Input sentence', 'Choose first language', 'Choose second language']
        loop = asyncio.get_event_loop()
        ret = loop.run_until_complete(trainer())
        # self.assertTrue(ret)
        self.assertEqual(ret, 201807271342)

if __name__ == '__main__':
    unittest.main()
