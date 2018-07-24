import aiohttp
import json

class TelegramBot(object):
    def __init__(self, token):
        self.token = token
        self.server_url = "http://localhost:5000"
        #await self.server_url = "http://langChainext-5c6a881e9c24431b.elb.ap-northeast-1.amazonaws.com:5000"

    async def __aenter__(self):
        # await asyncio.sleep(1.0)
        return   # __aenter__에서 값을 반환하면 as에 지정한 변수에 들어감

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def get_updates(self, last_update_id):
        api_get_updates = 'https://api.telegram.org/bot{}/getUpdates'.format(self.token)
        payloads = {'offset': last_update_id}
        async with aiohttp.ClientSession() as session:
            async with session.post(api_get_updates, data=payloads) as resp:
                res = await resp.json()
                msglist = res.get('result', [])
                return msglist

    async def send_message(self, chat_id, message):
        apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(self.token)
        payloads = {
            "chat_id": chat_id
            , "text": message
            , "parse_mode": "Markdown"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(apiEndpoint_send, data=payloads) as resp:
                return

    async def send_message_with_data(self, chat_id, message, params=None):
        apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(self.token)
        headers = {"Content-Type": "application/json"}
        payloads = {
            "chat_id": chat_id
            , "text": message
            , "parse_mode": "Markdown"
        }
        for key, value in params.items():
            payloads[key] = value

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(apiEndpoint_send, data=json.dumps(payloads)) as resp:
                return

    async def send_reply_message(self, chat_id, message_id, message):
        apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(self.token)
        payloads = {
                      "chat_id": chat_id
                    , "text": message
                    , "reply_to_message_id": message_id
                    , "parse_mode": "Markdown"
                  }
        async with aiohttp.ClientSession() as session:
            async with session.post(apiEndpoint_send, data=payloads) as resp:
                ret = await resp.json()
                return ret

    async def edit_message(self, chat_id, message_id, message):
        apiEndpoint_edit = "https://api.telegram.org/bot{}/editMessageText".format(self.token)
        payloads = {
            "chat_id": chat_id,
            "text": message,
            "message_id": message_id,
            "parse_mode": "Markdown"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(apiEndpoint_edit, data=payloads) as resp:
                return

    async def answer_callback_query(self, query_id):
        apiEndpoint_send = "https://api.telegram.org/bot{}/answerCallbackQuery".format(self.token)
        payloads = {
            "callback_query_id": query_id
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(apiEndpoint_send, data=json.dumps(payloads)) as resp:
                return

    async def set_language_keyboard(self, source_lang=None):
        lang_list = [
            {"text": "🇰🇷 Korean", "callback_data": "ko"},
            {"text": "🇺🇸 English", "callback_data": "en"},
            {"text": "🇯🇵 Japanese", "callback_data": "ja"},
            {"text": "🇨🇳 Chinese", "callback_data": "zh"},
            {"text": "🇹🇭 Thai", "callback_data": "th"},
            {"text": "🇪🇸 Spanish", "callback_data": "es"},
            {"text": "🇵🇹 Portuguese", "callback_data": "pt"},
            {"text": "🇻🇳 Vietnamese", "callback_data": "vi"},
            {"text": "🇩🇪 German", "callback_data": "de"},
            {"text": "🇫🇷 French", "callback_data": "fr"},
            {"text": "🇷🇺 Russian", "callback_data": "ru"},
            {"text": "🇮🇩 Indonesian", "callback_data": "id"}
        ]

        def make_array(arr, skip_idx=-1):
            ret = []
            temp_ret = []
            for idx, item in enumerate(lang_list):
                if idx != skip_idx and skip_idx == -1:
                    item['callback_data'] = '1st|{}'.format(item['callback_data'])
                    temp_ret.append(item)
                elif idx != skip_idx and skip_idx != -1:
                    item['callback_data'] = '2nd|{}'.format(item['callback_data'])
                    temp_ret.append(item)

                if len(temp_ret) == 3 and idx < len(lang_list) - 1:
                    ret.append(temp_ret)
                    temp_ret = []
            else:
                ret.append(temp_ret)
            return ret

        if source_lang == None:
            ret = make_array(lang_list)
        else:
            for idx, item in enumerate(lang_list):
                check_idx = -1
                if item['callback_data'] == source_lang:
                    check_idx = idx
                    break
            ret = make_array(lang_list, skip_idx=check_idx)
        return {"reply_markup": {"inline_keyboard": ret}}

    async def set_default_keyboard(self):
        return {
            "reply_markup": {
                "keyboard": [
                    ["💰My point", "✏️Translate", "⚙Set Language"]
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
        }

    async def langchain_get_id(self, id_external, chat_id=None, text_id=None):
        api_get_id = "{}/api/v1/getId".format(self.server_url)
        payloads = {
            "media": "telegram",
            "text_id": text_id,
            "id_external": id_external
        }
        if chat_id != None:
            payloads['chat_id'] = chat_id

        async with aiohttp.ClientSession() as session:
            async with session.post(api_get_id, data=payloads) as resp:
                ret = await resp.json()
                print(ret)
                return ret
