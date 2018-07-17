# -*- coding: utf-8 -*-
from app import connect_db
from flask import make_response, request, jsonify, session
import app.translator.models as model
from app.users.models import _getId, getPoint


def translateInternal():
    conn = connect_db()

    auth_key = request.headers.get('Authorization', None)
    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    user_id, is_internal = model.getApiKeyFromUser(conn, auth_key)
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
    is_ok, result = model.doWorkWithExternal(conn, source_lang, target_lang, sentence, user_id, where_contributed=where_contributed, order_user=order_user, media=media, tags=tags, memo=memo)

    if is_ok == True:
        return make_response(jsonify(**result), 200)

    else:
        return make_response(jsonify(message=""), 400)


def translateExternal():
    conn = connect_db()

    auth_key = request.headers.get('Authorization', None)
    if auth_key is None or auth_key == "":
        return make_response('No Auth Key', 503)

    user_id, is_internal = model.getApiKeyFromUser(conn, auth_key)
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
    is_ok, result = model.doWorkWithExternal(conn, source_lang, target_lang, sentence, user_id, where_contributed=where_contributed, order_user=order_user, media=media, tags=tags, memo=memo)

    if is_ok == True:
        return make_response(jsonify(result=result.get('ciceron')), 200)

    else:
        return make_response(jsonify(message=""), 400)


def getSentence():
    conn = connect_db()

    languages = request.args.get('languages', 'en')
    target_lang = request.args.get('target_lang', 'ko')
    media = request.args.get('media', 'web')
    id_external = request.args.get('id_external')
    text_id = request.args.get('text_id', 'anonymous')

    ret = model.getOneSentences( conn, media, id_external, languages, target_lang=target_lang, text_id=text_id )
    ret = ret if ret is not None else {}

    return make_response(jsonify(
        origin_text_id=ret.get('id'),
        contributor_media=ret.get('contributor_media'),
        contributor_text_id=ret.get('contributor_text_id'),
        text=ret.get('text'),
        origin_lang=ret.get('language'),
        where_contributed=ret.get('where_contributed'),
        tags=ret.get('tag')), 200)


def inputTranslation():
    if session.get('checked', False) == False and request.remote_addr != '127.0.0.1':
        return make_response(jsonify(result="fail"), 403)

    conn = connect_db()
    original_text_id = request.form['original_text_id']

    contributor_media = request.form['contributor_media']
    contributor_text_id = request.form.get('contributor_text_id')
    target_lang = request.form['target_lang']
    target_text = request.form['target_text']

    tags = request.form.get('tags')
    where_contribute = request.form.get('where_contribute')

    contributor_id_external = -1
    if request.form.get('contributor_external_id') is not None:
        contributor_id_external = int(request.form.get('contributor_external_id'))
    else:
        contributor_id_external = session.get('id_external', None)

    contributor_user_id_obj = _getId(conn, contributor_media, contributor_id_external, text_id=contributor_text_id)
    contributor_id = 0
    if contributor_user_id_obj is None or len(contributor_user_id_obj) < 1:
        contributor_id = 0
    else:
        contributor_id = contributor_user_id_obj['id']

    code, target_text_id, original_contributor_id, original_contributor_media, original_contributor_text_id, origin_lang, origin_text, origin_tag, origin_where_contributed, origin_id_external = model.inputTranslation(conn, original_text_id, contributor_id, target_text, target_lang, where_contribute, tags)

    if code == 0:
        if original_contributor_id == 0:
            is_ok = getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1.1, text_id=contributor_text_id)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'origin_contribute', 1, 0)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        else:
            is_ok = getPoint(conn, original_contributor_media, origin_id_external, origin_lang, target_lang, 0.1, text_id=original_contributor_text_id)
            is_ok = getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1, text_id=contributor_text_id)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = model.writeActionLog(conn, original_contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        ret_data = model.viewOneCompleteUnit(conn, target_text_id)

        if ret_data is not None:
            return make_response(jsonify(**ret_data), 200)
        else:
            return make_response(jsonify(result="nothing"), 200)

    else:
        return make_response(jsonify(result="nothing"), 200)


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
        return make_response(jsonify(error=error), 422)

    contributor_user_id_obj = _getId(conn, contributor_media, id_external=None, text_id=contributor_text_id)
    print(contributor_user_id_obj)
    contributor_id = 0
    if contributor_user_id_obj is None or len(contributor_user_id_obj) < 1:
        contributor_id = 0
    else:
        contributor_id = contributor_user_id_obj['id']

    code, target_text_id, original_contributor_id, original_contributor_media, original_contributor_text_id, origin_lang, origin_text, origin_tag, origin_where_contributed, origin_id_external = model.inputTranslation(conn, original_text_id, contributor_id, target_text, target_lang, where_contribute, tags)

    contributor_id_external = contributor_user_id_obj['id_external']
    if code == 0:
        if original_contributor_id == 0:
            is_ok = getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1.1, text_id=contributor_text_id)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'origin_contribute', 1, 0)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        else:
            is_ok = getPoint(conn, original_contributor_media, origin_id_external, origin_lang, target_lang, 0.1, text_id=original_contributor_text_id)
            is_ok = getPoint(conn, contributor_media, contributor_id_external, origin_lang, target_lang, 1, text_id=contributor_text_id)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'target_contribute', 1, 0)
            is_ok = model.writeActionLog(conn, original_contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 0.1)
            is_ok = model.writeActionLog(conn, contributor_id, None, origin_lang, target_lang, 'point_issue', 0, 1)

        ret_data = model.viewOneCompleteUnit(conn, target_text_id)

        if ret_data is not None:
            return make_response(jsonify(**ret_data), 200)
        else:
            return make_response(jsonify(result="nothing"), 200)

    else:
        return make_response(jsonify(result="nothing"), 200)


def completePariLog():
    conn = connect_db()

    page = request.args.get('page', 1)
    ret = model.viewCompleteTranslation(conn, int(page))
    return make_response(jsonify(data=ret), 200)
