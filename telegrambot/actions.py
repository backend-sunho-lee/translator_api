import asyncio
import requests
import json

class TelegramBot(object):
    def __init__(self, name, token):
        self.name = name
        self.token = token
        self.server_url = "http://localhost:5000"
        #await self.server_url = "http://langChainext-5c6a881e9c24431b.elb.ap-northeast-1.amazonaws.com:5000"

    async def __aenter__(self):
        await asyncio.sleep(1.0)
        return self.name  # __aenter__에서 값을 반환하면 as에 지정한 변수에 들어감

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def crawl_updates(self, last_update_id):
        api_get_updates = 'https://api.telegram.org/bot{}/getUpdates'.format(self.token)
        data = {'offset': last_update_id}
        resp = requests.post(api_get_updates, data=data)
        res = resp.json()
        msglist = res.get('result', [])
        return msglist

    async def _sendNormalMessage(self, chat_id, message):
        apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(self.token)
        payload = {
            "chat_id": chat_id
            , "text": message
            , "parse_mode": "Markdown"
        }
        requests.post(apiEndpoint_send, data=payload, timeout=1)

    async def _sendWithData(self, chat_id, message, params=None):
        apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(self.token)
        payload = {
            "chat_id": chat_id
            , "text": message
            , "parse_mode": "Markdown"
        }

        for key, value in params.items():
            payload[key] = value

        headers = {"Content-Type": "application/json"}
        requests.post(apiEndpoint_send, headers=headers, data=json.dumps(payload), timeout=1)

    async def _answerCallbackQuery(self, query_id):
        apiEndpoint_send = "https://api.telegram.org/bot{}/answerCallbackQuery".format(self.token)
        payload = {
            "callback_query_id": query_id
        }
        requests.post(apiEndpoint_send, data=payload, timeout=1)

    async def _getId(self, id_external, chat_id=None, text_id=None):
        payloads = {
            "media": "telegram"
            , "text_id": text_id
            , "id_external": id_external
        }
        if chat_id != None:
            payloads['chat_id'] = chat_id
        print(payloads)

        try:
            resp = requests.post("{}/api/v1/getId".format(self.server_url), data=payloads, timeout=1)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            await self._sendNormalMessage(chat_id, message_fail)
            return {}

        ret = resp.json()
        return ret

    async def crawlUpdate(self, offset):
        apiEndpoint_update = "https://api.telegram.org/bot{}/getUpdates".format(self.token)

        payload = {"offset": offset}
        resp = requests.post(apiEndpoint_update, data=payload)
        data = resp.json()
        ret = data.get('result', [])
        return ret

    async def newUser(self, chat_id, id_external, text_id=None):
        ret = await self._getId(id_external, chat_id=chat_id, text_id=text_id)
        message_success = "🙌Thanks to be a trainer of LangChain translation bot\n⚙Set your Language first."
        await self._sendNormalMessage(chat_id, message_success)

    async def setSourceLanguage(self, chat_id, id_external, lang, user_id=None):
        payloads = {
            "media": "telegram"
            , "text_id": user_id
            , "id_external": id_external
            , "language": lang
        }
        try:
            resp = requests.post("{}/api/v1/setSourceLanguage".format(self.server_url), data=payloads, timeout=1)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            await self._sendNormalMessage(chat_id, message_fail)
            return

    async def setTargetLanguage(self, chat_id, id_external, lang, user_id=None):
        payloads = {
            "media": "telegram"
            , "text_id": user_id
            , "language": lang
            , "id_external": id_external
        }
        try:
            resp = requests.post("{}/api/v1/setTargetLanguage".format(self.server_url), data=payloads, timeout=1)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            await self._sendNormalMessage(chat_id, message_fail)
            return

    async def languageSelect(self, source_lang=None):
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

        return {"reply_markup": {
            "inline_keyboard": ret
        }
        }

    async def normalKeyvoardSetting(self):
        return {"reply_markup": {
            "keyboard": [["💰My point", "✏️Translate", "⚙Set Language"]],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }
        }

    async def checkBalance(self, chat_id, id_external, text_id=None):
        ret = await self._getId(id_external, chat_id=chat_id, text_id=text_id)
        print(ret)

        balances = ret['point']
        total_point = 0
        for p in ret['point']:
            total_point += p['point']

        message = "You have *{}* points!\nThanks for your contribution!\n\n".format(round(total_point, 2))
        # message = "Here is your points!\nThanks for your contribution!\n\n"
        # message += "Total: *{}* points.\n\n".format(total_point)

        for item in balances:
            message += "{} → {}: *{}* points\n".format(item['source_lang'], item['target_lang'], item['point'])
        await self._sendNormalMessage(chat_id, message)

    async def getSentence(self, chat_id, id_external, text_id=None):
        ret = await self._getId(id_external, chat_id=chat_id, text_id=text_id)
        if ret is None:
            message_fail = "There seems a trouble to execute it. Please try again!"
            keyboard = await self.normalKeyvoardSetting()
            await self._sendWithData(chat_id, message_fail, params=keyboard)
            return

        source_lang = ret.get('source_lang')
        target_lang = ret.get('target_lang')

        if None in [source_lang, target_lang]:
            message = "❗️ Please ⚙Set Language first."
            keyboard = await self.normalKeyvoardSetting()
            await self._sendWithData(chat_id, message, params=keyboard)
            return
        elif source_lang == target_lang:
            message = "❗️ Setting Error. Please ⚙Set Language again."
            keyboard = await self.normalKeyvoardSetting()
            await self._sendWithData(chat_id, message, params=keyboard)
            return

        payloads = {
            "languages": source_lang
            , "target_lang": target_lang
            , "media": "telegram"
            , "text_id": text_id
            , "id_external": id_external
        }
        try:
            resp = requests.get("{}/api/v1/getSentence".format(self.server_url), params=payloads, timeout=5)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            await self._sendNormalMessage(chat_id, message_fail)
            return

        ret = resp.json()
        if ret['text'] is not None:
            message = "Please *translate* this sentence into *{}*:\n\n".format(target_lang)

            message += "*{}*\n\n".format(ret['text'])
            # message += "- Source media: {}\n".format(ret['where_contributed'])
            # message += "- Tags: {}".format(ret.get('tag'))

            message += "The point is recalled when abusing is detected.\nIf you want to _skip_ this sentence, click ✏️Translate button again."

        else:
            message = "Oops! There is no source sentence that matching language.\nPlease call @langchainbot for translation, then source sentence will be gathered!".format(
                target_lang)

        keyboard = await self.normalKeyvoardSetting()
        await self._sendWithData(chat_id, message, params=keyboard)

    async def clearLastSourceTextId(self, id_external, text_id=None):
        payloads = {
            "media": "telegram"
            , "text_id": text_id
            , "id_external": id_external
        }
        try:
            resp = requests.post("{}/api/v1/clearLastSentence".format(self.server_url), data=payloads, timeout=5)
        except:
            return

    async def inputSentence(self, chat_id, id_external, target_text, text_id=None, tags=""):
        ret = await self._getId(id_external, chat_id=chat_id, text_id=text_id)

        original_text_id = ret.get('last_original_text_id')
        if original_text_id is None:
            message = "Please press ✏️Translate button and contribute translation!"
            await self._sendNormalMessage(chat_id, message)
            return

        payload = {
            "original_text_id": original_text_id
            , "contributor_media": "telegram"
            , "contributor_text_id": text_id  # Legacy
            , "contributor_external_id": id_external
            , "target_lang": ret['target_lang']
            , "target_text": target_text
            , "tags": tags
            , "where_contribute": "telegram"
        }

        try:
            resp = requests.post("{}/api/v1/inputTranslation".format(self.server_url), data=payload, timeout=5)
            data = resp.json()

            # ret = await self._getId(id_external, chat_id=chat_id, text_id=text_id)
            # point_array = ret['point']
            # showing_point = 0.0
            # for item in point_array:
            #     if item['source_lang'] == ret['source_lang'] \
            #             and item['target_lang'] == ret['target_lang']:
            #         showing_point = item['point']
            #         break

            message = "Thanks for your contribution!\n"
            message += "You got *{}* point in {} → {} translation.".format(data['win_point'],
                                                                           data['source_lang'], data['target_lang'])
            await self._sendNormalMessage(chat_id, message)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            await self._sendNormalMessage(chat_id, message_fail)
            return
