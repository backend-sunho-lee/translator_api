import requests
import json


class TelegramBotAction(object):
    def __init__(self, api_key):
        self.domain = "http://localhost:5000"
        self.api_key = api_key

    def _sendNormalMessage(self, chat_id, message):
        apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(self.api_key)
        payload = { 
                      "chat_id": chat_id
                    , "text": message
                    , "parse_mode": "Markdown"
                  } 
        for _ in range(100):
            try:
                resp = requests.post(apiEndpoint_send, data=payload, timeout=5)
            except:
                continue

            if resp.status_code == 200:
                break

    def _sendWithData(self, chat_id, message, params=None):
        apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(self.api_key)
        payload = { 
                      "chat_id": chat_id
                    , "text": message
                    , "parse_mode": "Markdown"
                  }

        for key, value in params.items():
            payload[key] = value

        headers={"Content-Type": "application/json"}

        for _ in range(100):
            try:
                resp = requests.post(apiEndpoint_send, headers=headers,
                                                   data=json.dumps(payload), timeout=5)
            except:
                continue

            if resp.status_code == 200:
                break

    def _answerCallbackQuery(self, query_id):
        apiEndpoint_send = "https://api.telegram.org/bot{}/answerCallbackQuery".format(self.api_key)
        payload = { 
                    "callback_query_id": query_id
                  }

        for _ in range(100):
            try:
                resp = requests.post(apiEndpoint_send, data=payload, timeout=5)
            except:
                continue

            if resp.status_code == 200:
                break


    def _getId(self, text_id, chat_id=None):
        payloads = {
                "media": "telegram"
              , "text_id": text_id
                }
        if chat_id != None:
            payloads['chat_id'] = chat_id
    
        try:
            resp = requests.post("{}/api/v1/getId".format(self.domain), data=payloads, timeout=5)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            self._sendNormalMessage(chat_id, message_fail)
            return

        ret = resp.json()
        return ret
    
    def newUser(self, chat_id, text_id):
        ret = self._getId(text_id, chat_id)
        message_success = "Thanks to be a trainer of our LangChain translator!\nYou may start to do it after setting your language!"
        self._sendNormalMessage(chat_id, message_success)

    def setSourceLanguage(self, chat_id, user_id, lang):
        payloads = {
                "media": "telegram"
              , "text_id": user_id
              , "language": lang
                }
        try:
            resp = requests.post("{}/api/v1/setSourceLanguage".format(self.domain), data=payloads, timeout=5)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            self._sendNormalMessage(chat_id, message_fail)
            return

    def setTargetLanguage(self, chat_id, user_id, lang):
        payloads = {
                "media": "telegram"
              , "text_id": user_id
              , "language": lang
                }
        try:
            resp = requests.post("{}/api/v1/setTargetLanguage".format(self.domain), data=payloads, timeout=5)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            self._sendNormalMessage(chat_id, message_fail)
            return

    def languageSelect(self, source_lang=None):
        lang_list = [
                {"text":"🇰🇷 Korean", "callback_data":"ko"},
                {"text":"🇺🇸 English", "callback_data":"en"},
                {"text":"🇯🇵 Japanese", "callback_data":"ja"},
                {"text":"🇨🇳 Chinese", "callback_data":"zh"},
                {"text":"🇹🇭 Thai", "callback_data":"th"},
                {"text":"🇪🇸 Spanish", "callback_data":"es"},
                {"text":"🇵🇹 Portuguese", "callback_data":"pt"},
                {"text":"🇻🇳 Vietnamese", "callback_data":"vi"},
                {"text":"🇩🇪 German", "callback_data":"de"},
                {"text":"🇫🇷 French", "callback_data":"fr"},
                {"text":"🇷🇺 Russian", "callback_data":"ru"},
                {"text":"🇮🇩 Indonesian", "callback_data":"id"}
                    ]

        def make_array(arr, skip_idx= -1):
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

    def normalKeyvoardSetting(self):
        return {"reply_markup": {
                    "keyboard": [
                       ["Balance", "Translate", "Set Language"]
                                ],
                    "resize_keyboard": True,
                    "one_time_keyboard": False
                  }
                }

    def checkBalance(self, chat_id, text_id):
        ret = self._getId(text_id)
        balances = ret['point']

        message = "Here is your points!\nThanks for your contribution!\n\n"
        for item in balances:
            message += "{} -> {}: *{}* Points\n".format(item['source_lang'], item['target_lang'], item['point'])
        self._sendNormalMessage(chat_id, message)

    def getSentence(self, chat_id, text_id):
        ret = self._getId(text_id)
        source_lang = ret.get('source_lang')
        target_lang = ret.get('target_lang')

        payloads = {
                "languages": source_lang
              , "media": "telegram"
              , "text_id": text_id
                }
        try:
            resp = requests.get("{}/api/v1/getSentence".format(self.domain), params=payloads, timeout=5)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            self._sendNormalMessage(chat_id, message_fail)
            return

        ret = resp.json()
        if ret['text'] is not None:
            message = "Please translate this sentence into *{}*:\n\n".format(target_lang)

            message += "*{}*\n\n".format(ret['text'])
            message += "Source media: {}\n".format(ret['where_contributed'])
            message += "Tags: {}".format(ret.get('tag'))

        else:
            message = "Oops! There is no source sentence that matching language.\nPlease call @langchainbot for translation, then source sentence will be gathered!".format(target_lang)

        self._sendNormalMessage(chat_id, message)

    def inputSentence(self, chat_id, text_id,
            target_text,
            tags=""):

        ret = self._getId(text_id)

        original_text_id = ret['last_original_text_id']
        if original_text_id is None:
            message = "Please press 'Translate' button and contribute translation!"
            self._sendNormalMessage(chat_id, message)

        payload = {
              "original_text_id": original_text_id
            , "contributor_media": "telegram"
            , "contributor_text_id": text_id
            , "target_lang": ret['target_lang']
            , "target_text": target_text
            , "tags": tags
            , "where_contribute": "telegram"
        }

        try:
            resp = requests.post("{}/api/v1/inputTranslation".format(self.domain), data=payload, timeout=5)
        except:
            message_fail = "There seems a trouble to execute it. Please try again!"
            self._sendNormalMessage(chat_id, message_fail)
            return

        ret = self._getId(text_id)
        point_array = ret['point']
        showing_point = 0.0
        for item in point_array:
            if item['source_lang'] == ret['source_lang'] \
                    and item['target_lang'] == ret['target_lang']:
                showing_point = item['point']
                break

        message = "Thanks for your contribution!\nPoint: *{}* in {}->{} translation.".format(showing_point, ret['source_lang'], ret['target_lang'])
        self._sendNormalMessage(chat_id, message)
