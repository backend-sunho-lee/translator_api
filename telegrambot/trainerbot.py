import asyncio
import json
import time
from datetime import datetime

try:
    from actions import TelegramBot
except:
    from .actions import TelegramBot

with open('../config.json', 'r') as f:
    config = json.load(f)
TOKEN = config['telegram']['trainer']


def read_last_update_id():
    with open('trainer_update_id.txt', 'r') as f:
        last_update_id = f.read()
    return last_update_id

def write_last_update_id(last_update_id):
    with open('trainer_update_id.txt', 'w') as f:
        f.write(str(last_update_id))
    return

class TrainerBot(TelegramBot):
    async def __aenter__(self):
        last_update_id = int(read_last_update_id())
        msglist = await self.crawl_updates(last_update_id)

        if not msglist or len(msglist) == 0:
            return last_update_id

        futures = [asyncio.ensure_future(self.msg_handling(last_update_id, msg)) for msg in msglist]
        updatelist = await asyncio.gather(*futures)
        new_update_id = int(max(updatelist)) + 1
        return new_update_id

    async def msg_handling(self, new_lastUpdate_id, telegram_update):
        new_lastUpdate_id = max(new_lastUpdate_id, telegram_update.get('update_id'))

        if telegram_update.get('message') is not None:
            # Except 'select language'
            message_obj = telegram_update['message']
            chat_id = message_obj['chat']['id']
            sentence = message_obj.get('text')
            username = message_obj['from'].get('username')
            id_external = message_obj['from'].get('id')
            now = message_obj.get('date', datetime.utcnow())

            # if username is None or username == "":
            #    message = "Oops! You've not set your Telegram username.\nPlease go to *[menu → Setting → Username]*, set your username, and type '/start' again."
            #    await self._sendNormalMessage(chat_id, message)
            #    return make_response("OK", 200)

            if sentence is None:
                print("{} | {} | {} | {} | Multimedia Error".format(new_lastUpdate_id, now, id_external, username))
                message = "Currently we only take text data!\nYour interest and invenstment will be our fuel to develop useful tool such as OCR contributor or text extractor from sound!"
                await self._sendNormalMessage(chat_id, message)

            elif sentence == '/start':
                print("{} | {} | {} | {} | New user".format(new_lastUpdate_id, now, id_external, username))
                await self.newUser(chat_id, id_external, username)
                await self.clearLastSourceTextId(id_external, username)

                # Set source language
                message = "Which language do you want to translate *from*?"
                data = await self.languageSelect()
                await self._sendWithData(chat_id, message, params=data)

            elif sentence == '💰My point':
                print("{} | {} | {} | {} | Balance check".format(new_lastUpdate_id, now, id_external, username))
                await self.clearLastSourceTextId(id_external, username)
                await self.checkBalance(chat_id, id_external, username)

            elif sentence == '✏️Translate':
                print("{} | {} | {} | {} | Get sentence".format(new_lastUpdate_id, now, id_external, username))
                await self.getSentence(chat_id, id_external, text_id=username)

            elif sentence == '⚙Set Language':
                print("{} | {} | {} | {} | Set language".format(new_lastUpdate_id, now, id_external, username))
                await self.clearLastSourceTextId(id_external, text_id=username)
                ret = await self._getId(id_external, text_id=username)
                message = "*Current setting: {} → {}*\n\nWhich language do you want to translate *from*?".format(ret.get('source_lang'), ret.get('target_lang'))
                data = await self.languageSelect()
                await self._sendWithData(chat_id, message, params=data)

            else:
                print("{} | {} | {} | {} | Input sentence".format(new_lastUpdate_id, now, id_external, username))
                ret = await self._getId(id_external, text_id=username)
                # Translated sentence will input
                await self.inputSentence(chat_id, id_external, sentence, text_id=username, tags="telegram")
                await self.getSentence(chat_id, id_external, text_id=username)

        elif telegram_update.get('callback_query') is not None:
            # only for select language
            now = datetime.utcnow()
            query_obj = telegram_update['callback_query']
            message_obj = query_obj['message']

            chat_id = message_obj['chat']['id']
            query_id = query_obj['id']
            username = query_obj['from'].get('username')
            id_external = query_obj['from'].get('id')
            data_arr = query_obj['data'].split('|')
            await self.clearLastSourceTextId(id_external, text_id=username)

            seq = data_arr[0]
            lang = data_arr[1]

            if seq == '1st':
                print("{} | {} | {} | {} | Choose first language".format(new_lastUpdate_id, now, id_external, username))
                ret = await self._getId(id_external, text_id=username)
                # Store
                await self.setSourceLanguage(chat_id, id_external, lang, username)
                # await self._answerCallbackQuery(query_id)

                # Ask 2nd lang
                message = "Cool! You chose *{}*!\nThen, please choose one language that you want to translate *to*!".format(
                    lang)
                data = await self.languageSelect(source_lang=lang)
                await self._sendWithData(chat_id, message, params=data)

            elif seq == '2nd':
                print(
                    "{} | {} | {} | {} | Choose second language".format(new_lastUpdate_id, now, id_external, username))
                # Store
                await self.setTargetLanguage(chat_id, id_external, lang, username)
                # await self._answerCallbackQuery(query_id)
                ret = await self._getId(id_external, text_id=username)

                # Welcome message + show general keyboard
                message = "Settings are all done!\n*Current setting: {} → {}*\n\n".format(ret.get('source_lang'),
                                                                                          ret.get('target_lang'))
                message += "Please press ✏️Translate button below and earn point immediately!\n"
                message += "Point distribution details will be announced on Langchain page."
                # message += "*1. How to use it?*\n"
                # message += "Just press 'Translate' button and contribute data!\n\n"
                #
                # message += "*2. How much point can I earn?*\n"
                # message += "Source sentence contributor: *0.1 Point*.\n"
                # message += "Translated sentence contributor: *1 Point*.\n"
                # message += "If 2 contributors are same user: *1.1 Points*.\n"
                # message += "If I translated a sentence contributed by anonymous user: *1.1 Points*.\n\n"
                #
                # message += "*3. When can I use this point?*\n"
                # message += "Before launching LangChain, we'll take snapshot and give announcement about airdrop!\n"
                keyboard = await self.normalKeyvoardSetting()
                await self._sendWithData(chat_id, message, params=keyboard)

        return new_lastUpdate_id

async def main():
    async with TrainerBot('trainer', TOKEN) as new_update_id:  # async with에 클래스의 인스턴스 지정
        print(new_update_id)
        write_last_update_id(new_update_id)

while True:
    begin = time.time()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # loop.close()

    end = time.time()
    print('실행 시간: {0:.3f}초'.format(end - begin))

    time.sleep(0.5)
