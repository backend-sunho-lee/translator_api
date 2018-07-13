# -*- coding: utf-8 -*-

from flask import Flask, session, request, g, json, make_response, render_template, redirect
import os
import pymysql
from flask_cors import CORS
from flask_session import Session
from multiprocessing import Process
from datetime import datetime, timedelta

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

try:
    from users import Users
except:
    from .users import Users

try:
    from sentence import Sentences
except:
    from .sentence import Sentences



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
BOT_API_KEY = conf['telegram']['trainer']

app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = conf['app']['secret_key']
app.project_number = conf['google']['project_id']

Session(app)
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})
translator = Translator(GCM_API_KEY, BING_KEY)

def connect_db():
    return pymysql.connect(host=DATABASE['host'], user=DATABASE['user'], password=DATABASE['password'], db=DATABASE['db'], charset='utf8', cursorclass=pymysql.cursors.DictCursor)

def sendNormalMessage(chat_id, message):
    apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(BOT_API_KEY)
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

@app.route('/api/v2/internal/translate', methods=['POST'])
def translateInternal():
    conn = connect_db()

    auth_key = request.headers.get('Authorization', None)
    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    user_id, is_internal = ciceron_lib.getApiKeyFromUser(conn, auth_key)
    if user_id == -1 or is_internal == False:
        return make_response('Not Authorized', 403)

    client_ip = request.environ.get('REMOTE_ADDR')

    sentence = request.form['sentence']
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']
    tags = request.form.get('tag', "")
    order_user = request.form.get("order_user")
    media = request.form.get("media")
    where_contributed = request.form.get("where_contributed")
    memo = request.form.get('memo', "")

    # Real work
    is_ok, result = translator.doWorkWithExternal(conn, source_lang, target_lang, sentence, user_id, where_contributed=where_contributed, order_user=order_user, media=media, tags=tags, memo=memo)

    if is_ok == True:
        return make_response(json.jsonify(**result), 200)

    else:
        return make_response(json.jsonify(
            message=""), 400)


@app.route('/api/v2/external/translate', methods=['POST'])
def translateExternal():
    conn = connect_db()

    auth_key = request.headers.get('Authorization', None)
    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    user_id, is_internal = ciceron_lib.getApiKeyFromUser(conn, auth_key)
    if user_id == -1:
        return make_response('Not Authorized', 403)

    client_ip = request.environ.get('REMOTE_ADDR')

    #parameters = ciceron_lib.parse_request(request)
    sentence = request.form['sentence']
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']
    tags = request.form.get('tag', "")
    order_user = request.form.get("order_user")
    media = request.form.get("media")
    where_contributed = request.form.get("where_contributed")
    memo = request.form.get('memo', "")

    # Real work
    is_ok, result = translator.doWorkWithExternal(conn, source_lang, target_lang, sentence, user_id, where_contributed=where_contributed, order_user=order_user, media=media, tags=tags, memo=memo)

    if is_ok == True:
        return make_response(json.jsonify(result=result.get('ciceron')), 200)

    else:
        return make_response(json.jsonify(
            message=""), 400)

@app.route('/api/v1/setAuthCode', methods=['POST'])
def setAuthCode():
    conn = connect_db()
    media = request.form['media']
    id_external = request.form['id_external']
    text_id = request.form.get('text_id')

    userObj = Users()
    sentenceObj = Sentences()
    ret = sentenceObj.clearLastSentenceId( conn, media, id_external, text_id )
    is_ok, code, chat_id = userObj.setAuthCode(conn, media, id_external, text_id)
    if is_ok == False:
        return make_response(json.jsonify(result="fail"), 410)

    message  = "External login request!\n"
    message += "Please input following code:\n\n"
    message += "*{}*".format(code)
    sendNormalMessage(chat_id, message)

    return make_response(json.jsonify(result="ok"), 200)

@app.route('/api/v1/checkAuthCode', methods=['POST'])
def checkAuthCode():
    conn = connect_db()
    media = request.form['media']
    id_external = request.form['id_external']
    text_id = request.form.get('text_id')
    code = request.form['code']

    userObj = Users()
    sentenceObj = Sentences()
    ret = sentenceObj.clearLastSentenceId( conn, media, id_external, text_id )
    is_ok, chat_id = userObj.checkAuthCode(conn, media, id_external, code, text_id)

    if is_ok == True:
        session['checked'] = True
        session['media'] = media
        session['id_external'] = id_external

        message  = "✅ Successfully authenticated!"
        sendNormalMessage(chat_id, message)

        return make_response(json.jsonify(result="ok"), 200)

    else:
        message  = "❌ Wrong authentication trial is detected!"
        sendNormalMessage(chat_id, message)

        return make_response(json.jsonify(result="fail"), 403)

@app.route('/api/v1/logout', methods=['GET'])
def logout():
    session['checked'] = False
    return make_response(json.jsonify(result="ok"), 200)

@app.route('/api/v1/getId', methods=['POST'])
def getId():
    conn = connect_db()

    media = request.form['media']
    text_id = request.form.get('text_id')
    id_external = request.form['id_external']
    chat_id = request.form.get('chat_id')

    userObj = Users()
    ret = userObj.getId(conn, media, id_external, text_id)

    if chat_id != None:
        is_ok = userObj.setChatId(conn, media, id_external, chat_id, text_id)

    return make_response(json.jsonify(**ret), 200)

@app.route('/api/v1/setLanguage', methods=['POST'])
def setLanguage():
    conn = connect_db()

    media = request.form['media']
    id_external = request.form['id_external']
    languages = request.form['languages']
    text_id = request.form.get('text_id')
    userObj = Users()
    is_ok = userObj.setLanguage( conn, media, id_external, languages, text_id )
    if is_ok == True:
        return make_response(json.jsonify(result="ok"), 200)
    else:
        return make_response(json.jsonify(result="fail"), 410)

@app.route('/api/v1/setSourceLanguage', methods=['POST'])
def setSourceLanguage():
    conn = connect_db()

    media = request.form['media']
    id_external = request.form['id_external']
    languages = request.form['language']
    text_id = request.form.get('text_id')
    userObj = Users()
    is_ok = userObj.setSourceLanguage( conn, media, id_external, languages, text_id )
    if is_ok == True:
        return make_response(json.jsonify(result="ok"), 200)
    else:
        return make_response(json.jsonify(result="fail"), 410)

@app.route('/api/v1/setTargetLanguage', methods=['POST'])
def setTargetLanguage():
    conn = connect_db()

    media = request.form['media']
    id_external = request.form['id_external']
    languages = request.form['language']
    text_id = request.form.get('text_id')
    userObj = Users()
    is_ok = userObj.setTargetLanguage( conn, media, id_external, languages, text_id )

    user_dat = userObj.getId(conn, media, id_external, text_id)
    is_ok = userObj.getPoint(conn, media, id_external, user_dat['source_lang'], user_dat['target_lang'], 0, text_id)
    if is_ok == True:
        return make_response(json.jsonify(result="ok"), 200)
    else:
        return make_response(json.jsonify(result="fail"), 410)

@app.route('/api/v1/clearLastSentence', methods=['POST'])
def clearLastSentence():
    conn = connect_db()
    media = request.form['media']
    id_external = request.form['id_external']
    text_id = request.form.get('text_id')

    sentenceObj = Sentences()
    ret = sentenceObj.clearLastSentenceId( conn, media, id_external, text_id )
    return make_response(json.jsonify(result="ok"), 200)

@app.route('/api/v1/getSentence', methods=['GET'])
def getSentence():
    conn = connect_db()

    languages = request.args.get('languages', 'en')
    media = request.args.get('media', 'web')
    id_external = request.args.get('id_external')
    text_id = request.args.get('text_id', 'anonymous')

    sentenceObj = Sentences()
    ret = sentenceObj.getOneSentences( conn, media, id_external, languages, text_id )
    ret = ret if ret is not None else {}

    return make_response(json.jsonify(
        origin_text_id=ret.get('id'),
        contributor_media=ret.get('contributor_media'),
        contributor_text_id=ret.get('contributor_text_id'),
        text=ret.get('text'),
        origin_lang=ret.get('language'),
        where_contributed=ret.get('where_contributed'),
        tags=ret.get('tag')), 200)

@app.route('/api/v1/inputTranslation', methods=['POST'])
def inputTranslation():
    if session.get('checked', False) == False and request.remote_addr != '127.0.0.1':
        return make_response(json.jsonify(result="fail"), 403)

    conn = connect_db()
    original_text_id = request.form['original_text_id']

    contributor_media = request.form['contributor_media']
    contributor_text_id = request.form.get('contributor_text_id', None)
    target_lang = request.form['target_lang']
    target_text = request.form['target_text']

    tags = request.form.get('tags')
    where_contribute = request.form.get('where_contribute')

    contributor_id_external = -1
    if request.form.get('contributor_external_id') is not None:
        contributor_id_external = int(request.form.get('contributor_external_id'))
    else:
        contributor_id_external = session.get('id_external', None)

    print(contributor_id_external)

    sentenceObj = Sentences()
    userObj = Users()

    contributor_user_id_obj = userObj._getId(conn, contributor_media, contributor_id_external, text_id=contributor_text_id)
    contributor_id = 0
    if contributor_user_id_obj is None or len(contributor_user_id_obj) < 1:
        contributor_id = 0
    else:
        contributor_id = contributor_user_id_obj['id']

    code, target_text_id, original_contributor_id, original_contributor_media, original_contributor_text_id, origin_lang, origin_text, origin_tag, origin_where_contributed, origin_id_external = sentenceObj.inputTranslation(conn, original_text_id, contributor_id, target_text, target_lang, where_contribute, tags)

    if code == 0:
        if original_contributor_id == 0:
            is_ok = userObj.getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1.1, text_id=contributor_text_id)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'origin_contribute', 1, 0)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        else:
            is_ok = userObj.getPoint(conn, original_contributor_media, origin_id_external, origin_lang, target_lang, 0.1, text_id=original_contributor_text_id)
            is_ok = userObj.getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1, text_id=contributor_text_id)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = translator.writeActionLog(conn, original_contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        ret_data = translator.viewOneCompleteUnit(conn, target_text_id)

        if ret_data is not None:
            return make_response(json.jsonify(**ret_data), 200)
        else:
            return make_response(json.jsonify(result="nothing"), 200)

    else:
        return make_response(json.jsonify(result="nothing"), 200)

@app.route('/api/v1/translation/mycat', methods=['POST'])
def inputTranslation_from_mycat():
    """
    original_text_id: Int
    contributor_media: mycat
    contributor_email: 번역가 이메일
    tags: mycat에서 문서 입력시 받는 tags
    target_lang: 번역문 언어
    target_text:String, 번역문
    where_contribute:mycat
    :return:
    """
    conn = connect_db()
    original_text_id = request.form.get('original_text_id', None)

    contributor_media = request.form.get('contributor_media', None)
    contributor_text_id = request.form.get('contributor_text_id', None)
    target_lang = request.form.get('target_lang', None)
    target_text = request.form.get('target_text', None)
    where_contribute = request.form.get('where_contribute', None)

    tags = request.form.get('tags', None)

    if None in [original_text_id, contributor_media, contributor_text_id, target_lang, target_text, where_contribute]:
        error = {
            "code": 2301,
            "type": "NullValue",
            "message": "something not entered. please check source_id and comment."
        }
        return make_response(json.jsonify(error=error), 422)

    sentenceObj = Sentences()
    userObj = Users()

    contributor_user_id_obj = userObj._getId(conn, contributor_media, id_external=None, text_id=contributor_text_id)
    contributor_id = 0
    if contributor_user_id_obj is None or len(contributor_user_id_obj) < 1:
        contributor_id = 0
    else:
        contributor_id = contributor_user_id_obj['id']

    code, target_text_id, original_contributor_id, original_contributor_media, original_contributor_text_id, origin_lang, origin_text, origin_tag, origin_where_contributed, origin_id_external = sentenceObj.inputTranslation(conn, original_text_id, contributor_id, target_text, target_lang, where_contribute, tags)

    contributor_id_external = contributor_user_id_obj['id_external']
    if code == 0:
        if original_contributor_id == 0:
            is_ok = userObj.getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1.1, text_id=contributor_text_id)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'origin_contribute', 1, 0)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        else:
            is_ok = userObj.getPoint(conn, original_contributor_media, origin_id_external, origin_lang, target_lang, 0.1, text_id=original_contributor_text_id)
            is_ok = userObj.getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1, text_id=contributor_text_id)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = translator.writeActionLog(conn, original_contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = translator.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        ret_data = translator.viewOneCompleteUnit(conn, target_text_id)

        if ret_data is not None:
            return make_response(json.jsonify(**ret_data), 200)
        else:
            return make_response(json.jsonify(result="nothing"), 200)

    else:
        return make_response(json.jsonify(result="nothing"), 200)

@app.route('/api/v1/completePairLog', methods=['GET'])
def completePariLog():
    conn = connect_db()

    page = request.args.get('page', 1)
    ret = translator.viewCompleteTranslation(conn, int(page))
    return make_response(json.jsonify(data=ret), 200)

@app.route('/api/v1/actionLog', methods=['GET'])
def actionLog():
    conn = connect_db()

    page = request.args.get('page', 1)
    ret = translator.viewActionLog(conn, int(page))
    return make_response(json.jsonify(data=ret), 200)


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
