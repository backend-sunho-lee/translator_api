# -*- coding: utf-8 -*-
from app import app, azure
from app.users.models import _getId
import traceback
import pymysql
from datetime import datetime
import requests
import json
from xml.etree import ElementTree

import nltk
sentence_detector = nltk.data.load('tokenizers/punkt/english.pickle')

from googleapiclient.discovery import build
googleAPI = build('translate', 'v2', developerKey=app.config['GCM_API_KEY'])
bing_key = app.config['BING_KEY']
ciceronAPI_koen = "http://brutus.ciceron.xyz:5000/translate"
ciceronAPI_enko = "http://cicero.ciceron.xyz:5000/translate"


def getApiKeyFromUser(conn, apiKey):
    cursor = conn.cursor()
    query = """
        SELECT user_id, is_internal FROM
        auth_key
        WHERE api_key = %s
    """
    cursor.execute(query, (apiKey, ))
    ret = cursor.fetchone()
    if ret is None or len(ret) < 1:
        return -1, False
    else:
        return ret['user_id'], ret['is_internal']


def _inputOriginalSentence(conn, contributor_id, language,
        text, where_contributed, tags=""):
    cursor = conn.cursor()
    query = """
        INSERT INTO origin_texts
          (contributor_id, 
          language, 
          text, 
          count, 
          tag, 
          contributed_at, 
          text_hash, 
          where_contributed, 
          is_translated)

        VALUES
          (%s, 
           %s, 
           %s, 
           0, 
           %s, 
           CURRENT_TIMESTAMP, 
           MD5(%s), 
           %s, 
           false)
    """
    try:
        cursor.execute(query, (contributor_id, language, text, tags, text, where_contributed, ))

    except pymysql.err.IntegrityError:
        cursor.execute("""SELECT id as original_text_id FROM langchain.origin_texts WHERE text=%s;""", (text, ))
        ret = cursor.fetchone()
        print("Duplicate sentence {}".format(text))
        return 1, ret['original_text_id']

    except:
        traceback.print_exc()
        conn.rollback()
        return 2, None

    conn.commit()

    query_getId = "SELECT LAST_INSERT_ID() as last_id"
    cursor.execute(query_getId)
    ret = cursor.fetchone()
    if ret is None or len(ret) < 1:
        return 3, None

    return 0, ret['last_id']


def findTranslation(conn, origin_lang, target_lang, origin_text):
    cursor = conn.cursor()
    query = """
        SELECT 
            ori.id as original_text_id
          , tar.id as target_text_id
          , ori.contributor_id as origin_contributor_id
          , tar.contributor_id as target_contributor_id
          , ori.text as origin_text
          , tar.text as target_text
          , ori.contributed_at as origin_contributed_at
          , tar.contributed_at as target_contributed_at
        FROM langchain.origin_text_users ori
        RIGHT OUTER JOIN langchain.target_text_users tar ON ori.id = tar.origin_text_id
        WHERE
              ori.language = %s
          AND tar.language = %s
          AND ori.text_hash = MD5(%s)
        ORDER BY RAND()
        LIMIT 1
    """
    cursor.execute(query, (origin_lang, target_lang, origin_text, ))
    ret = cursor.fetchone()
    if ret is None or len(ret) < 1:
        return False, None, None, None, None, None

    original_text_id = ret['original_text_id']
    target_text_id = ret['target_text_id']
    original_contributor_id = ret['origin_contributor_id']
    target_contributor_id = ret['target_contributor_id']
    origin_text = ret['origin_text']
    target_text = ret['target_text']
    origin_contributed_at = ret['origin_contributed_at']
    target_contributed_at = ret['target_contributed_at']

    return True, original_text_id, target_text_id, original_contributor_id, target_contributor_id, origin_text, target_text, origin_contributed_at, target_contributed_at


def increaseSearchCnt(conn, origin_text_id):
    cursor = conn.cursor()
    query = """
        UPDATE origin_texts
          set count = count + 1
        WHERE
          id = %s
    """
    try:
        cursor.execute(query, (origin_text_id, ))
    except:
        traceback.print_exc()
        conn.rollback()
        return False

    conn.commit()
    return True


def writeActionLog(conn, user_id, object_user_id,
                   origin_lang, target_lang,
                   action_name, sentence_amount, point_amount):
    cursor = conn.cursor()
    query = """
        INSERT INTO action_log
          (   executed_at
            , user_id
            , object_user_id
            , origin_lang
            , target_lang
            , action_name
            , sentence_amount
            , point_amount
          )
        VALUES
          (   CURRENT_TIMESTAMP
            , %s
            , %s
            , %s
            , %s
            , %s
            , %s
            , %s
          )
    """
    try:
        cursor.execute(query, (user_id, object_user_id,
                               origin_lang, target_lang,
                               action_name, sentence_amount, point_amount, ))

    except:
        traceback.print_exc()
        conn.rollback()
        return False

    conn.commit()
    return True


def getLangCode(platform, lang_code):
    if platform == 'google' and lang_code == 'zh':
        return 'zh-CN'

    elif platform == 'bing' and lang_code == 'zh':
        return 'zh-CHS'

    else:
        return lang_code


def _googleTranslate(source_lang, target_lang, sentences):
    cur_time = datetime.now()
    google_source_lang = getLangCode('google', source_lang)
    google_target_lang = getLangCode('google', target_lang)
    result_google = googleAPI.translations().list(
        source=google_source_lang,
        target=google_target_lang,
        q=sentences
    ).execute()
    fin_time = datetime.now()
    print("Google: {} seconds".format((fin_time - cur_time).total_seconds()))
    if result_google.get('translations') != None:
        result_text = result_google['translations'][0]['translatedText']
        return result_text
    else:
        return None


def _ciceronTranslate(source_lang, target_lang, sentence):
    payload = {
        'sentence': sentence
        , 'source_lang': source_lang
        , 'target_lang': target_lang
    }

    headers = {'content-type': 'application/json'}

    cur_time = datetime.now()
    API = None
    print(source_lang, target_lang)
    if source_lang == 'ko' and target_lang == 'en':
        API = ciceronAPI_koen
    elif source_lang == 'en' and target_lang == 'ko':
        API = ciceronAPI_enko
    else:
        return ""

    try:
        response = requests.post(API, data=json.dumps(payload), headers=headers, timeout=5)
    except:
        traceback.print_exc()
        return "Check translator connection status"

    fin_time = datetime.now()

    print("Ciceron: {} seconds".format((fin_time - cur_time).total_seconds()))

    data = response.json() if response.status_code == 200 else None
    if source_lang == 'ko' and target_lang == 'en':
        return_sentences = data.get('translated_result') if data is not None else " "
        print("Result: {}".format(return_sentences))
        return_sentences = return_sentences[0].upper() + return_sentences[1:]
        return_sentences = return_sentences.replace('"', "")

    else:
        return_sentences = data.get('translated_result') if data is not None else ""

    return return_sentences


def _bingTranslate(source_lang, target_lang, sentences):
    bing_source_lang = getLangCode('bing', source_lang)
    bing_target_lang = getLangCode('bing', target_lang)
    auth_client = azure.AzureAuthClient(bing_key)

    cur_time = datetime.now()
    bearer_token = 'Bearer ' + auth_client.get_access_token().decode('utf-8')
    headers = {"Authorization ": bearer_token}
    translateUrl = "http://api.microsofttranslator.com/v2/Http.svc/Translate?text={}&from={}&to={}".format(
        sentences, source_lang, target_lang)

    translationData = requests.get(translateUrl, headers=headers)
    fin_time = datetime.now()

    print("Bing: {} seconds".format((fin_time - cur_time).total_seconds()))

    # parse xml return values
    translation = ElementTree.fromstring(translationData.text.encode('utf-8'))

    return translation.text


def doWorkSingle(source_lang, target_lang, sentences):
    result_google  = _googleTranslate(source_lang, target_lang, sentences)
    result_bing    = _bingTranslate(source_lang, target_lang, sentences)
    result_ciceron = _ciceronTranslate(source_lang, target_lang, sentences)

    return True, {
                     'google': result_google
                   , 'bing': result_bing
                   , 'ciceron': result_ciceron
                   #, 'papago': result_papago.get()
                   , 'papago': None
                 }


def recordToTranslationLog(conn, source_lang, target_lang, sentences
             , google_result, bing_result, ciceron_result, human_correction_result
             , memo, tags, user_id
             , is_db_used, complete_sentence_id):

    cursor = conn.cursor()
    query = """
        INSERT INTO translation_log
            (  source_lang
             , target_lang
             , original_text
             , google_result
             , bing_result
             , ciceron_result
             , human_correction_result
             , memo
     , user_id
             , executed_at
             , is_db_used
             , complete_sentence_id
             )
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
    """
    try:
        cursor.execute(query,
                (source_lang, target_lang,
                 sentences,
         google_result,
         bing_result,
         ciceron_result,
                 human_correction_result,
                 memo,
         user_id,
                 is_db_used,
                 complete_sentence_id,
         )
                )
    except:
        traceback.print_exc()
        conn.rollback()
        return False

    conn.commit()
    return True


def increaseCallCnt(conn, user_id):
    cursor = conn.cursor()
    query = """
        UPDATE auth_key
          set cnt = cnt + 1
        WHERE
          user_id = %s
    """
    try:
        cursor.execute(query, (user_id, ))
    except:
        traceback.print_exc()
        conn.rollback()
        return False

    conn.commit()
    return True


def doWorkWithExternal(conn, source_lang, target_lang, sentences, user_id, where_contributed=None,
                       order_user=None, media=None, memo="", tags=""):

    # is_ok, result = doWork(source_lang_id, target_lang_id, sentences)

    # 상용구를 찾는다
    # 상용구가 있으면
    #   1. complete_sentence  카운트 올린다
    #   2. Action에 기록한다
    #   3. translation_log에 상용구 데이터 찾았다는 표시와 함께 기록한다.
    #   4. API call cnt

    # 상용구가 없으면
    #   1. original_text에 등록한다
    # .  2. Action에 기록한다
    # .  3. translation_log에 기록한다.
    #   4. API call cnt

    ret = _getId(conn, media, order_user)

    order_user_id = 0
    if ret is None or len(ret) < 1:
        order_user_id = 0
    else:
        order_user_id = ret['id']

    splitted_sentence = sentence_detector.tokenize(sentences)
    searched_sentences = []

    for idx, sentence in enumerate(splitted_sentence):
        ret = findTranslation(conn, source_lang, target_lang, sentence)
        original_text_id = ret[1]

        # 0: True,
        # 1: original_text_id
        # 2: target_text_id
        # 3: origin_contributor_id
        # 4: target_contributor_id
        # 5: origin_text
        # 6: target_textwriteActionLog
        # 7: origin_contributed_at
        # 8: target_contributed_at

        if ret[0] == True:  # is_ok
            dat = {"seq": idx, "data": ret}
            searched_sentences.append(dat)
            is_ok = increaseSearchCnt(conn, ret[1])
            is_ok = writeActionLog(conn, order_user_id, ret[4], source_lang, target_lang, 'refer', 1, 0)

        else:
            code, original_text_id = _inputOriginalSentence(conn, order_user_id, source_lang,
                                                                            sentence, where_contributed, tags)
            if code == 0:
                is_ok = writeActionLog(conn, order_user_id, 0, source_lang, target_lang, 'origin_contribute',
                                            1, 0)
            elif code == 1:
                # Duplicate origin lang contribution
                # 태그 로직 반영되면 변경예정
                pass
            else:
                return False, None

    is_ok, result = doWorkSingle(source_lang, target_lang, sentences)
    result['original_text_id'] = original_text_id

    splitted_translated_sentence = []
    if (source_lang == 'ko' and target_lang == 'en') or (source_lang == 'en' and target_lang == 'ko'):
        splitted_translated_sentence = sentence_detector.tokenize(result.get('ciceron'))

    else:
        splitted_translated_sentence = sentence_detector.tokenize(result.get('google'))

    if len(searched_sentences) > 0:
        for item in searched_sentences:
            splitted_translated_sentence[item['seq']] = item['data'][6]

        result['human'] = ' '.join(splitted_translated_sentence)

    else:
        result['human'] = None

    is_db_used = True if len(searched_sentences) > 0 else False
    complete_sentence_ids = ','.join([str(item['data'][2]) for item in searched_sentences])

    is_ok = recordToTranslationLog(
        conn, source_lang, target_lang, sentences,
        result.get('google'), result.get('bing'), result.get('ciceron'), result.get('human'),
        memo, tags, user_id, is_db_used, complete_sentence_ids
    )

    is_ok = increaseCallCnt(conn, user_id)
    return is_ok, result


def getOneSentences(conn, media, id_external, origin_lang, target_lang=None, text_id=None):
    cursor = conn.cursor()
    query = """
        SELECT *
        FROM origin_text_users
        WHERE language = %s
             AND id NOT IN (
                        SELECT origin_text_id 
                        FROM (
                              SELECT origin_text_id, count(*) AS cnt 
                              FROM target_text_users
                              WHERE language = %s
                             GROUP BY origin_text_id
                                   ) tmp
                        WHERE cnt >= 1
                      )
        ORDER BY RAND()
        LIMIT 1
    """
    cursor.execute(query, (origin_lang, target_lang, ))
    ret = cursor.fetchone()

    query_updateId = """
        UPDATE users
          SET last_original_text_id = %s,
              text_id = %s,
              last_connected_time = CURRENT_TIMESTAMP 
        WHERE media = %s AND id_external = %s
    """
    try:
        cursor.execute(query_updateId, (ret['id'], text_id, media, int(id_external), ))
    except:
        traceback.print_exc()
        conn.rollback()
        return {}

    conn.commit()
    return ret


def viewOneCompleteUnit(conn, target_text_id, page=1):
    cursor = conn.cursor()
    query = """
        SELECT 
            ori.id as original_text_id
          , tar.id as target_text_id
          , ori.contributor_id as origin_contributor_id
          , tar.contributor_id as target_contributor_id
          , ori.text as origin_text
          , tar.text as target_text
          , ori.contributed_at as origin_contributed_at
          , tar.contributed_at as target_contributed_at
        FROM langchain.origin_text_users ori
        RIGHT OUTER JOIN langchain.target_text_users tar ON ori.id = tar.origin_text_id
        WHERE
              tar.id = %s
        LIMIT 1
    """
    cursor.execute(query, ( target_text_id, ))
    return cursor.fetchone()


def viewCompleteTranslation(conn, page=1):
    cursor = conn.cursor()
    query = """
        SELECT *
        FROM complete_sentence_users
        ORDER BY added_at DESC
        LIMIT 20
        OFFSET %s
    """.format(page)
    cursor.execute(query, ( 20 * (page-1), ))
    return cursor.fetchall()


def _inputTargetSentence(conn, contributor_id, original_text_id, language,
        text, where_contributed, tags=""):
    cursor = conn.cursor()
    query = """
        INSERT INTO target_text
          (contributor_id, 
          origin_text_id, 
          language,
          text, 
          confirm_cnt,
          tags, 
          contributed_at, 
          where_contributed)

        VALUES
          (%s, 
           %s, 
           %s, 
           %s,
           0, 
           %s, 
           CURRENT_TIMESTAMP, 
           %s)
    """
    try:
        cursor.execute(query, (contributor_id, original_text_id, language, text, tags, where_contributed, ))
    except pymysql.err.IntegrityError:
        print("Duplicate sentence {}".format(text))
        return False, None

    except:
        traceback.print_exc()
        conn.rollback()
        return False, None

    query_getId = "SELECT LAST_INSERT_ID() as last_id"
    cursor.execute(query_getId)
    ret = cursor.fetchone()
    if ret is None or len(ret) < 1:
        return False, None

    return True, ret['last_id']


def _getOriginSentenceInfo(conn, origin_text_id):
    cursor = conn.cursor()
    query = """
        SELECT * FROM origin_text_users
        WHERE id = %s
        LIMIT 1
    """
    cursor.execute(query, (origin_text_id, ))
    return cursor.fetchone()


def _markAsTranslated(conn, origin_text_id):
    cursor = conn.cursor()
    query = """
        UPDATE origin_texts
          SET is_translated = true
        WHERE id = %s
    """
    try:
        cursor.execute(query, (origin_text_id, ))
    except:
        traceback.print_exc()
        conn.rollback()
        return False

    return True


def inputTranslation(conn,
        original_text_id,
        target_contributor_id, target_text, target_lang,
        where_contribute,
        tags=""):
    is_ok, target_text_id = _inputTargetSentence(conn, target_contributor_id, original_text_id, target_lang, target_text, where_contribute, tags)

    ret = _getOriginSentenceInfo(conn, original_text_id)
    if ret is None or len(ret) < 1:
        return False, None, None, None, None, None

    original_contributor_id = ret['contributor_id']
    original_contributor_media = ret['contributor_media']
    original_contributor_text_id = ret['contributor_text_id']
    origin_lang = ret['language']
    origin_text = ret['text']
    origin_tag = ret['tag']
    origin_where_contributed = ret['where_contributed']
    origin_contributor_id_external = ret['contributor_id_external']

    is_ok = _markAsTranslated(conn, original_text_id)

    #code, complete_id = _inputCompleteSentence(conn,
    #        original_text_id, target_text_id,
    #        original_contributor_id, target_contributor_id,
    #        origin_lang, target_lang,
    #        origin_text, target_text,
    #        origin_tag, tags,
    #        origin_where_contributed, where_contribute)

    conn.commit()

    query_getId = "SELECT LAST_INSERT_ID() as last_id"
    cursor = conn.cursor()
    cursor.execute(query_getId)
    ret = cursor.fetchone()
    if ret is None or len(ret) < 1:
        return 3, None

    last_id = ret['last_id']

    return 0, last_id, original_contributor_id, original_contributor_media, original_contributor_text_id, origin_lang, origin_text, origin_tag, origin_where_contributed, origin_contributor_id_external
