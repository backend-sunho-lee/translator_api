# -*- coding: utf-8 -*-

from flask import Flask, session, request, g, json, make_response, render_template, redirect
import os
import pymysql
from flask_cors import CORS
from flask_session import Session
from multiprocessing import Process
from datetime import datetime

import requests
import json as pyjson

try:
    from . import ciceron_lib
except:
    import ciceron_lib

try:
    from function import TelegramBotAction
except:
    from .function import TelegramBotAction


conf = {}
with open('config.json', 'r') as f:
    conf = pyjson.load(f)

DATABASE = conf['db']
BOT_API_KEY = conf['telegram']['trainer']

VERSION = '1.1'
DEBUG = True
GCM_API_KEY = conf['google']['key']
BING_KEY = conf['bing']['key']
SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "cicerontranslator"

app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = conf['app']['secret_key']
app.project_number = conf['google']['project_id']

Session(app)
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})

def connect_db():
    return pymysql.connect(host=DATABASE['host'], user=DATABASE['user'], password=DATABASE['password'], db=DATABASE['db'], charset='utf8', cursorclass=pymysql.cursors.DictCursor)

@app.before_request
def before_request():
    #if request.url.startswith('http://'):
    #    url = request.url.replace('http://', 'https://', 1)
    #    code = 301
    #    return redirect(url, code=code)

    pass

@app.teardown_request
def teardown_request(exception):
    """
    모든 API 실행 후 실행하는 부분. 여기서는 DB 연결종료.
    """
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def checkAuth(conn, key):
    cursor = conn.cursor()
    query = """
        SELECT count(*) as cnt
        FROM auth_key
        WHERE api_key = %s
    """
    cursor.execute(query, (key, ))
    ret = cursor.fetchone()
    if ret is None or len(ret) < 1:
        return False

    cnt = ret['cnt']
    if cnt == 1:
        return True
    else:
        return False

@app.route('/api/v2/external/telegram/<auth_key>/webhook', methods=['POST'])
def webHook(auth_key):
    conn = connect_db()

    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    is_auth_activated = checkAuth(conn, auth_key)
    if is_auth_activated == False:
        return make_response('Invalid key', 403)

    telegram_update = request.get_json()
    actionCtrl = TelegramBotAction(BOT_API_KEY)

    # Main logic
    if telegram_update.get('message') is not None:
        # Except 'select language'
        message_obj = telegram_update['message']
        chat_id = message_obj['chat']['id']
        sentence = message_obj['text']
        username = message_obj['from']['username']

        if username is None or username == "":
            message = "Oops! You've not set your Telegram username.\nPlease go to *[menu -> Setting -> Username]*, set your username, and type '/start' again."
            actionCtrl._sendNormalMessage(chat_id, message)

        elif sentence == '/start':
            actionCtrl.newUser(chat_id, username)

            # Set source language
            message = "Which language do you want to traslate from?"
            data = actionCtrl.languageSelect()
            actionCtrl._sendWithData(chat_id, message, params=data)

        elif sentence == 'Balance':
            actionCtrl.clearLastSourceTextId(username)
            actionCtrl.checkBalance(chat_id, username)

        elif sentence == 'Translate':
            actionCtrl.getSentence(chat_id, username)

        elif sentence == 'Set Language':
            actionCtrl.clearLastSourceTextId(username)
            ret = actionCtrl._getId(username)
            message = "Current setting: *{}* -> *{}*\n\nWhich language do you want to traslate from?".format(ret['source_lang'], ret['target_lang'])
            data = actionCtrl.languageSelect()
            actionCtrl._sendWithData(chat_id, message, params=data)

        else:
            # Translated sentence will input
            actionCtrl.inputSentence(chat_id, username, sentence, tags="telegram")
            actionCtrl.getSentence(chat_id, username)

    elif telegram_update.get('callback_query') is not None:
        actionCtrl.clearLastSourceTextId(username)
        # only for select language
        query_obj = telegram_update['callback_query']
        message_obj = query_obj['message']

        chat_id = message_obj['chat']['id']
        query_id = query_obj['id']
        username = query_obj['from']['username']
        data_arr = query_obj['data'].split('|')

        seq = data_arr[0]
        lang = data_arr[1]

        if seq == '1st':
            # Store
            actionCtrl.setSourceLanguage(chat_id, username, lang)
            actionCtrl._answerCallbackQuery(query_id)

            # Ask 2nd lang
            message = "Cool! Then, please choose one language that you want to translate to!"
            data = actionCtrl.languageSelect(source_lang=lang)
            actionCtrl._sendWithData(chat_id, message, params=data)

        elif seq == '2nd':
            # Store
            actionCtrl.setTargetLanguage(chat_id, username, lang)
            actionCtrl._answerCallbackQuery(query_id)

            # Welcome message + show general keyboard
            ret = actionCtrl._getId(username)
            message  = "Settings are all done!\nCurrent setting: *{}* -> *{}*\n\nPlease press 'Translate' button below and earn point immediately!\n\n".format(ret['source_lang'], ret['target_lang'])
            message += "*1. How to use it?*\n"
            message += "Just press 'Translate' button and contribute data!\n\n"

            message += "*2. How much point can I earn?*\n"
            message += "Source sentence contributor: *0.1 Point*.\n"
            message += "Translated sentence contributor: *1 Point*.\n"
            message += "If 2 contributors are same user: *1.1 Points*.\n"
            message += "If I translated a sentence contributed by anonymous user: *1.1 Points*.\n\n"

            message += "*3. When can I use this point?*\n"
            message += "Before launching LangChain, we'll take snapshot and give announcement about airdrop!\n"
            keyboard = actionCtrl.normalKeyvoardSetting()
            actionCtrl._sendWithData(chat_id, message, params=keyboard)

    return make_response("OK", 200)


if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer
    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    cert = './cert/chained_translator_ciceron_me2.pem'
    key = './cert/pfx.translator_ciceron_me.key'
    context.load_cert_chain(cert, key)

    http_server = WSGIServer(('0.0.0.0', 8443), app, ssl_context=context)
    #http_server = WSGIServer(('0.0.0.0', 8443), app)
    http_server.serve_forever()
    # Should be masked!
    #app.run(host="0.0.0.0", port=80)
    
