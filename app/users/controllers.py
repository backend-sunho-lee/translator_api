# -*- coding: utf-8 -*-
from app import app, connect_db
from flask import request, make_response, jsonify, session
import app.users.models as model
import requests

BOT_API_KEY = app.config['BOT_API_KEY']


def sendNormalMessage(chat_id, message):
    apiEndpoint_send = "https://api.telegram.org/bot{}/sendMessage".format(BOT_API_KEY)
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    for _ in range(100):
        try:
            resp = requests.post(apiEndpoint_send, data=payload, timeout=5)
        except:
            continue

        if resp.status_code == 200:
            break


def setAuthCode():
    conn = connect_db()
    media = request.form['media']
    id_external = request.form['id_external']
    text_id = request.form.get('text_id')

    ret = model.clearLastSentenceId( conn, media, id_external, text_id )
    is_ok, code, chat_id = model.setAuthCode(conn, media, id_external, text_id)
    if is_ok == False:
        return make_response(jsonify(result="fail"), 410)

    message  = "External login request!\n"
    message += "Please input following code:\n\n"
    message += "*{}*".format(code)
    sendNormalMessage(chat_id, message)

    return make_response(jsonify(result="ok"), 200)


def checkAuthCode():
    conn = connect_db()
    media = request.form['media']
    id_external = request.form['id_external']
    text_id = request.form.get('text_id')
    code = request.form['code']

    ret = model.clearLastSentenceId(conn, media, id_external, text_id)
    is_ok, chat_id = model.checkAuthCode(conn, media, id_external, code, text_id)

    if is_ok == True:
        session['checked'] = True
        session['media'] = media
        session['id_external'] = id_external

        message  = "✅ Successfully authenticated!"
        sendNormalMessage(chat_id, message)

        return make_response(jsonify(result="ok"), 200)

    else:
        message  = "❌ Wrong authentication trial is detected!"
        sendNormalMessage(chat_id, message)

        return make_response(jsonify(result="fail"), 403)


def getId():
    conn = connect_db()

    media = request.form['media']
    text_id = request.form.get('text_id')
    id_external = request.form['id_external']
    chat_id = request.form.get('chat_id')

    ret = model.getId(conn, media, id_external, text_id)

    if chat_id != None:
        is_ok = model.setChatId(conn, media, id_external, chat_id, text_id)

    return make_response(jsonify(**ret), 200)


def setLanguage():
    conn = connect_db()

    media = request.form['media']
    id_external = request.form['id_external']
    languages = request.form['languages']
    text_id = request.form.get('text_id')

    is_ok = model.setLanguage( conn, media, id_external, languages, text_id )
    if is_ok == True:
        return make_response(jsonify(result="ok"), 200)
    else:
        return make_response(jsonify(result="fail"), 410)


def setSourceLanguage():
    conn = connect_db()

    media = request.form['media']
    id_external = request.form['id_external']
    languages = request.form['language']
    text_id = request.form.get('text_id')

    is_ok = model.setSourceLanguage( conn, media, id_external, languages, text_id )
    if is_ok == True:
        return make_response(jsonify(result="ok"), 200)
    else:
        return make_response(jsonify(result="fail"), 410)


def setTargetLanguage():
    conn = connect_db()

    media = request.form['media']
    id_external = request.form['id_external']
    languages = request.form['language']
    text_id = request.form.get('text_id')

    is_ok = model.setTargetLanguage( conn, media, id_external, languages, text_id )

    user_dat = model.getId(conn, media, id_external, text_id)
    is_ok = model.getPoint(conn, media, id_external, user_dat['source_lang'], user_dat['target_lang'], 0, text_id)
    if is_ok == True:
        return make_response(jsonify(result="ok"), 200)
    else:
        return make_response(jsonify(result="fail"), 410)


def clearLastSentence():
    conn = connect_db()
    media = request.form['media']
    id_external = request.form['id_external']
    text_id = request.form.get('text_id')

    ret = model.clearLastSentenceId( conn, media, id_external, text_id )
    return make_response(jsonify(result="ok"), 200)


def actionLog():
    conn = connect_db()

    page = request.args.get('page', 1)
    ret = model.viewActionLog(conn, int(page))
    return make_response(jsonify(data=ret), 200)
