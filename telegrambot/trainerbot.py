import asyncio
import aiohttp
import json
from datetime import datetime

try:
    from actions import TelegramBot
except:
    from .actions import TelegramBot

with open('../config.json', 'r') as f:
    config = json.load(f)
TOKEN = config['telegram']['trainer']

class TrainerBot(TelegramBot):
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
        with open('updateid_trainer.txt', 'r') as f:
            last_update_id = f.read()
        return last_update_id

    async def write_last_update_id(self, last_update_id):
        with open('updateid_trainer.txt', 'w') as f:
            f.write(str(last_update_id))
        return

    async def get_user_point(self, chat_id, id_external, text_id=None):
        ret = await self.langchain_get_id(id_external, chat_id=chat_id, text_id=text_id)

        balances = ret['point']
        total_point = 0
        for p in ret['point']:
            total_point += p['point']

        message = "You have *{}* points!\nThanks for your contribution!\n\n".format(round(total_point, 2))
        for item in balances:
            message += "{} → {}: *{}* points\n".format(item['source_lang'], item['target_lang'], item['point'])
        await self.send_message(chat_id, message)

    async def langchain_get_sentence_to_translate(self, chat_id, id_external, text_id=None):
        ret = await self.langchain_get_id(id_external, chat_id=chat_id, text_id=text_id)
        if ret is None:
            message_fail = "There seems a trouble to execute it. Please try again!"
            keyboard = await self.set_default_keyboard()
            await self.send_message_with_data(chat_id, message_fail, params=keyboard)
            return

        source_lang = ret.get('source_lang', None)
        target_lang = ret.get('target_lang', None)

        if None in [source_lang, target_lang]:
            message = "❗️ Please ⚙Set Language first."
            keyboard = await self.set_default_keyboard()
            await self.send_message_with_data(chat_id, message, params=keyboard)
            return
        elif source_lang == target_lang:
            message = "❗️ Setting Error. Please ⚙Set Language again."
            keyboard = await self.set_default_keyboard()
            await self.send_message_with_data(chat_id, message, params=keyboard)
            return

        api_get_sentence = "{}/api/v1/getSentence".format(self.server_url)
        payloads = {
            "languages": source_lang
            , "target_lang": target_lang
            , "media": "telegram"
            , "text_id": text_id
            , "id_external": id_external
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(api_get_sentence, params=payloads) as resp:
                if resp.status != 200:
                    message_fail = "There seems a trouble to execute it. Please try again!"
                    await self.send_message(chat_id, message_fail)
                    return
                ret = await resp.json()
                # print(ret)

                if ret['text'] is not None:
                    message = "Please *translate* this sentence into *{}*:\n\n".format(target_lang)
                    message += "*{}*\n\n".format(ret['text'])
                    # message += "- Source media: {}\n".format(ret['where_contributed'])
                    # message += "- Tags: {}".format(ret.get('tag'))
                    message += "The point is recalled when abusing is detected.\nIf you want to _skip_ this sentence, click ✏️Translate button again."
                else:
                    message = "Oops! There is no source sentence that matching language."
                    message += "Please call @langchainbot for translation, then source sentence will be gathered!".format(target_lang)

                keyboard = await self.set_default_keyboard()
                await self.send_message_with_data(chat_id, message, params=keyboard)
                return

    async def langhcain_clear_last_sentence(self, id_external, text_id=None):
        payloads = {
            "media": "telegram"
            , "text_id": text_id
            , "id_external": id_external
        }
        api_clear_last_sentence = "{}/api/v1/clearLastSentence".format(self.server_url)
        async with aiohttp.ClientSession() as session:
            async with session.post(api_clear_last_sentence, data=payloads) as resp:
                return

    async def langchain_input_translate(self, chat_id, id_external, target_text, text_id=None, tags=""):
        ret = await self.langchain_get_id(id_external, chat_id=chat_id, text_id=text_id)

        original_text_id = ret.get('last_original_text_id')
        if original_text_id is None:
            message = "Please press ✏️Translate button and contribute translation!"
            await self.send_message(chat_id, message)
            return

        api_input_translation = "{}/api/v1/inputTranslation".format(self.server_url)
        payloads = {
            "original_text_id": original_text_id
            , "contributor_media": "telegram"
            , "contributor_text_id": text_id  # Legacy
            , "contributor_external_id": id_external
            , "target_lang": ret['target_lang']
            , "target_text": target_text
            , "tags": tags
            , "where_contribute": "telegram"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(api_input_translation, data=payloads) as resp:
                if resp.status != 200:
                    message_fail = "There seems a trouble to execute it. Please try again!"
                    await self.send_message(chat_id, message_fail)
                    return

                data = await resp.json()
                message = "Thanks for your contribution!\n"
                message += "You got *{}* point in {} → {} translation.".format(data['win_point'],
                                                                               data['source_lang'], data['target_lang'])
                await self.send_message(chat_id, message)
                return

    async def langchain_set_source_lang(self, chat_id, id_external, lang, user_id=None):
        api_set_source_language = "{}/api/v1/setSourceLanguage".format(self.server_url)
        payloads = {
            "media": "telegram"
            , "text_id": user_id
            , "id_external": id_external
            , "language": lang
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(api_set_source_language, data=payloads) as resp:
                if resp.status != 200:
                    # print('setsourcelang', resp.status)
                    message_fail = "There seems a trouble to execute it. Please try again!"
                    await self.send_message(chat_id, message_fail)
                return

    async def langchain_set_target_lang(self, chat_id, id_external, lang, user_id=None):
        api_set_target_language = "{}/api/v1/setTargetLanguage".format(self.server_url)
        payloads = {
            "media": "telegram"
            , "text_id": user_id
            , "language": lang
            , "id_external": id_external
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(api_set_target_language, data=payloads) as resp:
                if resp.status != 200:
                    # print('settargetlang', resp.status)
                    message_fail = "There seems a trouble to execute it. Please try again!"
                    await self.send_message(chat_id, message_fail)
                return

    async def msg_handling(self, obj):
        update_id = obj.get('update_id')

        if obj.get('message') is not None:
            # Except 'select language'
            msg = obj['message']
            msg_date = msg.get('date', datetime.utcnow())
            text = msg.get('text')
            id_external = msg['from'].get('id')
            username = msg['from'].get('username')
            chat_id = msg['chat']['id']

            if text is None:
                print("{} | {} | {} | {} | Multimedia Error".format(update_id, msg_date, id_external, username))
                message = "Currently we only take text data!\nYour interest and invenstment will be our fuel to develop useful tool such as OCR contributor or text extractor from sound!"
                await self.send_message(chat_id, message)

            elif text == '/start':
                print("{} | {} | {} | {} | New user".format(update_id, msg_date, id_external, username))
                await self.langchain_get_id(id_external, chat_id)
                await self.langhcain_clear_last_sentence(id_external, username)
                message_success = "🙌Thanks to be a trainer of LangChain translation bot\n⚙Set your Language first."
                await self.send_message(chat_id, message_success)

                # Set source language
                message = "Which language do you want to translate *from*?"
                data = await self.set_language_keyboard()
                await self.send_message_with_data(chat_id, message, params=data)

            elif text == '💰My point':
                print("{} | {} | {} | {} | Balance check".format(update_id, msg_date, id_external, username))
                await self.langhcain_clear_last_sentence(id_external, username)
                await self.get_user_point(chat_id, id_external, username)

            elif text == '✏️Translate':
                print("{} | {} | {} | {} | Get sentence".format(update_id, msg_date, id_external, username))
                await self.langchain_get_sentence_to_translate(chat_id, id_external, text_id=username)

            elif text == '⚙Set Language':
                print("{} | {} | {} | {} | Set language".format(update_id, msg_date, id_external, username))
                await self.langhcain_clear_last_sentence(id_external, text_id=username)
                ret = await self.langchain_get_id(id_external, text_id=username)
                message = "*Current setting: {} → {}*\n\nWhich language do you want to translate *from*?".format(ret.get('source_lang'), ret.get('target_lang'))
                data = await self.set_language_keyboard()
                await self.send_message_with_data(chat_id, message, params=data)

            else:
                print("{} | {} | {} | {} | Input sentence".format(update_id, msg_date, id_external, username))
                ret = await self.langchain_get_id(id_external, text_id=username)
                # Translated sentence will input
                await self.langchain_input_translate(chat_id, id_external, text, text_id=username, tags="telegram")
                await self.langchain_get_sentence_to_translate(chat_id, id_external, text_id=username)

        elif obj.get('callback_query') is not None:
            # only for select language
            msg_date = datetime.utcnow()
            query_obj = obj['callback_query']
            msg = query_obj['message']

            chat_id = msg['chat']['id']
            query_id = query_obj['id']
            username = query_obj['from'].get('username')
            id_external = query_obj['from'].get('id')
            data_arr = query_obj['data'].split('|')
            await self.langhcain_clear_last_sentence(id_external, text_id=username)

            seq = data_arr[0]
            lang = data_arr[1]

            if seq == '1st':
                print("{} | {} | {} | {} | Choose first language".format(update_id, msg_date, id_external, username))
                ret = await self.langchain_get_id(id_external, text_id=username)
                # Store
                await self.langchain_set_source_lang(chat_id, id_external, lang, username)

                # Ask 2nd lang
                message = "Cool! You chose *{}*!\nThen, please choose one language that you want to translate *to*!".format(lang)
                data = await self.set_language_keyboard(source_lang=lang)
                await self.send_message_with_data(chat_id, message, params=data)

            elif seq == '2nd':
                print("{} | {} | {} | {} | Choose second language".format(update_id, msg_date, id_external, username))
                # Store
                await self.langchain_set_target_lang(chat_id, id_external, lang, username)
                # await self.answer_callback_query(query_id)
                ret = await self.langchain_get_id(id_external, text_id=username)

                # Welcome message + show general keyboard
                message = "Settings are all done!\n*Current setting: {} → {}*\n\n".format(ret.get('source_lang'),
                                                                                          ret.get('target_lang'))
                message += "Please press ✏️Translate button below and earn point immediately!\n"
                message += "Point distribution details will be announced on Langchain page."
                keyboard = await self.set_default_keyboard()
                await self.send_message_with_data(chat_id, message, params=keyboard)
        return update_id

async def main():
    async with TrainerBot(TOKEN) as new_update_id:  # async with에 클래스의 인스턴스 지정
        return new_update_id

if __name__ == '__main__':
    while True:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        # loop.close()
