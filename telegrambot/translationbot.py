import asyncio
import aiohttp
import json
import time
from datetime import datetime
import re
import os
cwd = os.getcwd()
cwd = cwd.split('/')
if cwd[-1] != '_translator_api':
    cwd[-1] = '_translator_api'
    cwd = '/'.join(cwd)
    os.chdir(cwd)
else:
    cwd = '/'.join(cwd)

try:
    from actions import TelegramBot
except:
    from .actions import TelegramBot

with open('config.json', 'r') as f:
    config = json.load(f)
TOKEN = config['telegram']['translator']
CICERON_API_KEY = config['ciceron']['translator']

LANGUAGES = ['ko', 'en', 'zh', 'ja', 'ru', 'in', 'de', 'th', 'fr', 'vi', 'es', 'pt']
LANGUES_SET = """🇰🇷 ko \t🇺🇸 en  🇨🇳 zh  🇯🇵 ja
🇷🇺 ru\t\t🇮🇩 in\t\t\t🇩🇪 de  🇹🇭 th
🇫🇷 fr\t\t\t🇻🇳 vi\t\t\t🇪🇸 es\t\t 🇵🇹 pt"""

HOW_TO_USE = """✔️How to use
!'Source language''Target language' 'Sentence'
Ex) *!enko It's such a beautiful day*

{}

📌You can get _frontier points_ by using the Translation bot.
📌Please put _sentence by sentence_.
""".format(LANGUES_SET)

class TranslationBot(TelegramBot):
    async def __aenter__(self):
        last_update_id = await self.read_last_update_id()
        last_update_id = int(last_update_id)
        msglist = await self.get_updates(last_update_id)

        if not msglist or len(msglist) == 0:
            return last_update_id

        futures = [asyncio.ensure_future(self.msg_handling(msg)) for msg in msglist]
        updatelist = await asyncio.gather(*futures)

        if updatelist:
            max_update_id = max(updatelist)
            if max_update_id >= last_update_id:
                new_update_id = int(max_update_id) + 1
            else:
                new_update_id = last_update_id
        else:
            new_update_id = last_update_id
        await self.write_last_update_id(new_update_id)
        return new_update_id

    async def read_last_update_id(self):
        with open('updateid_translation.txt', 'r') as f:
            last_update_id = f.read()
        return last_update_id

    async def write_last_update_id(self, last_update_id):
        with open('updateid_translation.txt', 'w') as f:
            f.write(str(last_update_id))
        return

    async def _translate(self, id_external, source_lang, target_lang, sentence, order_user, memo):
        payloads = {
                    "source_lang": source_lang
                  , "target_lang": target_lang
                  , "sentence": sentence
                  , "tag": "telegram"
                  , "order_user": order_user
                  , "id_external": id_external
                  , "media": "telegram"
                  , "where_contributed": "telegram"
                  , "memo": memo
                }
        headers = {"Authorization": CICERON_API_KEY}

        async with aiohttp.ClientSession(headers=headers) as session:
            api_internal_translate = "{}/api/v2/internal/translate".format(self.server_url)
            async with session.post(api_internal_translate, data=payloads, verify_ssl=False) as resp:
                if resp.status != 200:
                    data = {
                        "ciceron": "Not enough servers. Investment is required.",
                        "google": None,
                        "human": None
                    }
                else:
                    data = await resp.json()

        result_google = data.get('google', None)
        result_human = data.get('human', None)

        if result_human is not None:
            # print('human', result_human)
            message = "*{}*\n\n".format(result_human)
        else:
            # print('google', result_google)
            message = "*{}*\n\n".format(result_google)

        message += "_Powered by_ @LangChainTrainerbot"
        return message

    async def msg_handling(self, obj):
        update_id = obj.get('update_id')
        msg = obj.get('message', None)
        if msg is None:
            return

        msg_date = msg.get('date', datetime.utcnow())
        chat_id = msg['chat']['id']
        message_id = msg['message_id']
        text = msg.get('text')
        username = msg.get('from').get('username')
        chat_type = msg['chat']['type']
        group_title = msg['chat'].get('title')
        id_external = msg['from'].get('id')

        if text is None:
            return
        else:
            text = text.strip()

        if text == '/start' or text == '/help':
            print("{} | {} | {} | {} | New user".format(update_id, msg_date, id_external, username))
            user_info = await self.langchain_get_id(id_external, chat_id=chat_id, text_id=username)
            message_usage = "*Hi, It’s LangChain Bot*👋\n"
            message_usage += "Use translation bot without any external translation app!\n\n"
            message_usage += HOW_TO_USE
            await self.send_message(chat_id, message_usage)

        elif text.startswith('!'):
            print("{} | {} | {} | {} | Translate".format(update_id, msg_date, id_external, username))
            lang_obj = re.search(r'\A!([a-z]{2})([a-z]{2})', text)
            if lang_obj == None: return

            language_pair = lang_obj.group(0)
            source_lang = lang_obj.group(1)
            target_lang = lang_obj.group(2)

            if source_lang not in LANGUAGES or target_lang not in LANGUAGES:
                message = 'You send wrong language code. Try again.\n\n{}'.format(LANGUES_SET)
                # print(message)
                await self.send_reply_message(chat_id, message_id, message)
                return update_id

            text = text.replace(language_pair, '').strip()
            # print(text)
            if not text or text == ' ':
                message = 'Please enter message to translate.'
                # print(message)
                await self.send_reply_message(chat_id, message_id, message)
                await self.send_reply_message(chat_id, message_id, HOW_TO_USE)
                return update_id

            ret = await self.send_reply_message(chat_id, message_id, "_Translating..._\n\n" + HOW_TO_USE)
            new_chat_id = ret['result']['chat']['id']
            new_message_id = ret['result']['message_id']

            message = await self._translate(id_external, source_lang, target_lang, text, username,
                                      "Telegram:{}|{}|{}".format(username, chat_type, group_title))
            # print(message)
            await self.edit_message(new_chat_id, new_message_id, message)
        return update_id

async def main():
    async with TranslationBot(TOKEN) as new_update_id:  # async with에 클래스의 인스턴스 지정
        return new_update_id

if __name__ == "__main__":
    while True:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        # loop.close()
