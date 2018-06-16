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
    from translator import Translator
except:
    from .translator import Translator

conf = {}
with open('config.json', 'r') as f:
    conf = pyjson.load(f)

DATABASE = conf['db']

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

translator = Translator(GCM_API_KEY, BING_KEY)

def connect_db():
    return pymysql.connect(**DATABASE)

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

@app.route('/')
def index():
    return render_template('layout.html', translateText=None)

# Legacy
@app.route('/translate', methods=['POST'])
def translate():
    conn = connect_db()
    recorder = VoteTranslationResult(conn)

    client_ip = request.environ.get('REMOTE_ADDR')
    #if client_ip not in ['52.196.144.144', '121.128.220.114']:
    #    return make_response(json.jsonify(
    #        message='Unauthorized'), 401)

    #parameters = ciceron_lib.parse_request(request)
    user_email = request.form['user_email']
    sentence = request.form['sentence']
    source_lang_id = request.form['source_lang_id']
    target_lang_id = request.form['target_lang_id']
    memo = request.form.get('memo')

    if source_lang_id is not None:
        source_lang_id = int(source_lang_id)

    if target_lang_id is not None:
        target_lang_id = int(target_lang_id)

    is_ok, result = translator.doWorkSingle(source_lang_id, target_lang_id, sentence)

    if is_ok == False:
        return make_response(json.jsonify(
            message=""), 400)

    else:
        source_lang = get_lang_id(source_lang_id)
            target_lang = get_lang_id(target_lang_id)
            recorder.write(source_lang, target_lang, sentence,
                    result.get('google'),
                    result.get('bing'),
                    result.get('ciceron'),
                    memo=memo)
                    None)
        return make_response(json.jsonify(**result), 200)


@app.route('/api/v2/internal/translate', methods=['POST'])
def translateInternal():
    conn = connect_db()

    auth_key = request.headers.get('Authorization', None)
    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    user_id, is_internal = ciceron_lib.getApiKeyFromUser(g.db, auth_key)
    if user_id == -1 or is_internal == False:
        return make_response('Not Authorized', 403)

    client_ip = request.environ.get('REMOTE_ADDR')

    sentence = request.form['sentence']
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']
    tags = request.form.get('tag', "")
    memo = request.form.get('memo', "")

    # Real work
    is_ok, result = translator.doWorkWithExternal(conn, source_lang, target_lang, sentence, user_id, tags, memo)

    if is_ok == True:
        return make_response(json.jsonify(**result), 200)

    else:
        return make_response(json.jsonify(
            message=""), 400)


@app.route('/api/v2/external/translate', methods=['POST'])
def translateExternal():
    conn = connect_db()
    conn = None

    auth_key = request.headers.get('Authorization', None)
    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    user_id, is_internal = ciceron_lib.getApiKeyFromUser(g.db, auth_key)
    if user_id == -1:
        return make_response('Not Authorized', 403)

    client_ip = request.environ.get('REMOTE_ADDR')

    #parameters = ciceron_lib.parse_request(request)
    sentence = request.form['sentence']
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']
    tags = request.form.get('tag', "")
    memo = request.form.get('memo', "")

    # Real work
    is_ok, result = translator.doWorkWithExternal(conn, source_lang, target_lang, sentence, user_id, tags, memo)

    if is_ok == True:
        return make_response(json.jsonify(result=result.get('ciceron')), 200)

    else:
        return make_response(json.jsonify(
            message=""), 400)

@app.route('/api/v2/external/telegram/<auth_key>/webhook', methods=['POST'])
def webHook(auth_key):
    conn = connect_db()

    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    telegram_update = request.get_json()
    
    if auth_key.startswith("CCR-6177F4F8") and auth_key.endswith("6945FD2BD"):
        API_ENDPOINT = "https://api.telegram.org/bot575363781:AAGCIxEWupZhjlqBJwPvD6eM_Lin3jXdFnE/sendMessage"
        source_lang = 'ko'
        target_lang = 'en'

    chat_id = telegram_update['message']['chat']['id']
    sentence = telegram_update['message']['text']

    # Real work
    is_ok, result = translator.doWorkWithExternal(conn, source_lang, target_lang, sentence, auth_key)

    result_ciceron = result.get('ciceron')
    result_google = result.get('google')
    message = "LangChain:\n{}\n\nGoogle:\n{}".format(result_ciceron, result_google)

    resp = requests.post(API_ENDPOINT, data={"chat_id": chat_id, "text":message}, timeout=5)

    if is_ok == True:
        return make_response("OK", 200)

    else:
        return make_response("Fail", 410)


if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer
    import ssl
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    #cert = './cert/pfx.translator_ciceron.me.crt'
    #key = './cert/pfx.translator_ciceron_me.key'
    #context.load_cert_chain(cert, key)

    #http_server = WSGIServer(('0.0.0.0', 443), app, ssl_context=context)
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
    # Should be masked!
    #app.run(host="0.0.0.0", port=80)
