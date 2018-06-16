# -*- coding: utf-8 -*-

from flask import Flask, session, request, g, json as flaskjson, make_response, render_template
from googleapiclient.discovery import build
#from yandex_translate import YandexTranslate
import os
import traceback
import requests
import json
from xml.etree import ElementTree
from multiprocessing import Process, Queue
from datetime import datetime, timedelta

try:
    from urllib.parse import quote
except:
    from urllib import quote

try:
    from . import ciceron_lib
except:
    import ciceron_lib


class Translator(object):
    def __init__(self, google_key, bing_key):
        self.googleAPI = build('translate', 'v2',
                                developerKey=google_key)
        self.bing_key = bing_key
        self.ciceronAPI_koen = "http://brutus.ciceron.xyz:5000/translate"
        self.ciceronAPI_enko = "http://cicero.ciceron.xyz:5000/translate"


    def getLangCode(self, platform, lang_code):
        if platform == 'google' and lang_code == 'zh':
            return 'zh-CN'
    
        elif platform == 'bing' and lang_code == 'zh':
            return 'zh-CHS'
    
        else:
            return lang_code

    def _googleTranslate(self, source_lang, target_lang, sentences):
        cur_time = datetime.now()
        google_source_lang = self.getLangCode('google', source_lang)
        google_target_lang = self.getLangCode('google', target_lang)
        result_google = self.googleAPI.translations().list(
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

    def _ciceronTranslate(self, source_lang, target_lang, sentence):
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
            API = self.ciceronAPI_koen
        elif source_lang == 'en' and target_lang == 'ko':
            API = self.ciceronAPI_enko
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

    def _bingTranslate(self, source_lang, target_lang, sentences):
        bing_source_lang = self.getLangCode('bing', source_lang)
        bing_target_lang = self.getLangCode('bing', target_lang)
        auth_client = ciceron_lib.AzureAuthClient(self.bing_key)

        cur_time = datetime.now()
        bearer_token = 'Bearer ' + auth_client.get_access_token().decode('utf-8')
        headers = {"Authorization ": bearer_token}
        translateUrl = "http://api.microsofttranslator.com/v2/Http.svc/Translate?text={}&from={}&to={}".format(sentences, source_lang, target_lang)
    
        translationData = requests.get(translateUrl, headers = headers)
        fin_time = datetime.now()

        print("Bing: {} seconds".format((fin_time - cur_time).total_seconds()))

        # parse xml return values
        translation = ElementTree.fromstring(translationData.text.encode('utf-8'))

        return translation.text

    #def _yandexTranslate(self, source_lang, target_lang, sentences):
    #    lang_FromTo = '%s-%s' % (source_lang, target_lang)
    #    result_yandex = self.yandexAPI.translate(sentences, lang_FromTo)
    #    if result_yandex.get('text') != None:
    #        return result_yandex['text'][0]
    #    else:
    #        return None

    def doWork(self, source_lang, target_lang, sentences):
        def translation_job(func, source_lang, target_lang, sentence, queue):
            queue.put(func(source_lang, target_lang, sentence))

        result_google = Queue()
        result_bing = Queue()
        result_ciceron = Queue()
        #result_papago = Queue()

        try:
            job_google = Process(target=translation_job,
                                 args=(self._googleTranslate, source_langCodeDict['google'], target_langCodeDict['google'], sentences, result_google)
                                 )
        except Exception:
            traceback.print_exc()
            print("Err in Google")
            result_google.put("초벌번역 처리가 불가능한 문자가 삽입되었습니다. / Unsupported character is contained in the sentence.")

        try:
            job_bing = Process(target=translation_job,
                               args=(self._bingTranslate, source_langCodeDict['bing'], target_langCodeDict['bing'], sentences, result_bing)
                               )
        except Exception:
            traceback.print_exc()
            print("Err in Bing")
            result_bing.put("초벌번역 처리가 불가능한 문자가 삽입되었습니다. / Unsupported character is contained in the sentence.")

        #try:
        #    result_yandex = self._yandexTranslate(source_langCodeDict['yandex'], target_langCodeDict['yandex'], sentences)
        #except Exception:
        #    traceback.print_exc()
        #    result_yandex = "초벌번역 처리가 불가능한 문자가 삽입되었습니다. / Unsupported character is contained in the sentence."

        try:
            job_ciceron = Process(target=translation_job,
                                         args=(self._ciceronTranslate, source_langCodeDict['google'], target_langCodeDict['google'], sentences, result_ciceron)
                                         )
        except Exception:
            traceback.print_exc()
            print("Err in CICERON")
            result_ciceron.put("초벌번역 처리가 불가능한 문자가 삽입되었습니다. / Unsupported character is contained in the sentence.")

        #try:
        #    job_papago = Process(target=translation_job,
        #                                 args=(self._papagoTranslate, source_langCodeDict['google'], target_langCodeDict['google'], sentences, result_papago)
        #                                 )

        #except Exception:
        #    traceback.print_exc()
        #    result_papago.put("초벌번역 처리가 불가능한 문자가 삽입되었습니다. / Unsupported character is contained in the sentence.")

        job_ciceron.start()
        job_google.start()
        job_bing.start()
        #job_papago.start()

        job_ciceron.join()
        job_google.join()
        job_bing.join()
        #job_papago.join()

        return True, {
                         'google': result_google.get()
                       , 'bing': result_bing.get()
                       #, 'yandex': result_yandex
                       , 'ciceron': result_ciceron.get()
                       #, 'papago': result_papago.get()
                       , 'papago': None
                     }

    def doWorkSingle(self, source_lang, target_lang, sentences):
        result_google  = self._googleTranslate(source_lang, target_lang, sentences)
        result_bing    = self._bingTranslate(source_lang, target_lang, sentences)
        result_ciceron = self._ciceronTranslate(source_lang, target_lang, sentences)

        return True, {
                         'google': result_google
                       , 'bing': result_bing
                       , 'ciceron': result_ciceron
                       #, 'papago': result_papago.get()
                       , 'papago': None
                     }

    def recordToDb(self, conn, source_lang, target_lang, sentences
                 , google_result, bing_result, ciceron_result, memo, tags, user_id):

        cursor = conn.cursor()
        query = """
            INSERT INTO F_TRANSLATOR_RESULT
                (  source_lang
                 , target_lang
                 , original_text
                 , google_result
                 , bing_result
                 , ciceron_result
                 , tags
                 , memo
		 , user_id
                 , executed_at
                 )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        try:
            cursor.execute(query,
                    (source_lang, target_lang,
                     sentences,
		     google_result,
		     bing_result,
		     ciceron_result,
                     tags,
                     memo,
		     user_id, 
		     )
                    )
        except:
            traceback.print_exc()
            conn.rollback()
            conn.close()
            return False

        conn.commit()
        return True

    def doWorkWithExternal(self, conn, source_lang, target_lang, sentences, user_id, memo="", tags=""):
        
        #is_ok, result = self.doWork(source_lang_id, target_lang_id, sentences)
        is_ok, result = self.doWorkSingle(source_lang, target_lang, sentences)
        is_ok = self.recordToDb(
                    conn, source_lang, target_lang, sentences,
                    result.get('google'), result.get('bing'), result.get('ciceron'),
                    memo, tags, user_id
                )

        return is_ok, result


class VoteTranslationResult(object):
    def __init__(self, conn):
        self.conn = conn

    def write(self, source_lang, target_lang, 
                    original_text,
                    google_result, bing_result, ciceron_result, papago_result, memo=None):
        cursor = self.conn.cursor()
        new_id = ciceron_lib.get_new_id(self.conn, 'F_TRANSLATOR_RESULT')
        query = """
            INSERT INTO CICERON.F_TRANSLATOR_RESULT
                (  id
                 , source_lang
                 , target_lang
                 , original_text
                 , google_result
                 , bing_result
                 , ciceron_result
                 , papago_result
                 , memo
                 , executed_at
                 )
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """
        try:
            cursor.execute(query,
                    (new_id, source_lang, target_lang, 
                     original_text, google_result, bing_result, ciceron_result, papago_result, memo, )
                    )
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False, None

        self.conn.commit()

        return True, new_id

    def vote(self, result_id, versus, vote_to):
        cursor = self.conn.cursor()
        query = """
            UPDATE CICERON.F_TRANSLATOR_RESULT
            SET
                versus = %s
              , vote_to = %s
            WHERE
              id = %s
        """
        try:
            cursor.execute(query, (versus, vote_to, result_id, ))
        except:
            traceback.print_exc()
            self.conn.rollback()
            return False

        return True


class VoteTranslationResultAPI(object):
    def __init__(self, app, endpoints):
        self.app = app
        self.endpoints = endpoints

        self.add_api(self.app)

    def add_api(self, app):
        for endpoint in self.endpoints:
            self.app.add_url_rule('{}/user/translator/store'.format(endpoint), view_func=self.translatorStore, methods=["POST"])
            self.app.add_url_rule('{}/user/translator/vote'.format(endpoint), view_func=self.translatorVote, methods=["POST"])

    def translatorStore(self):
        voteTranslationResultObj = VoteTranslationResult(g.db)
        parameters = ciceron_lib.parse_request(request)

        source_lang = parameters['source_lang']
        target_lang = parameters['target_lang']
        original_text = parameters['original_text']
        google_result = parameters['google_result']
        bing_result = parameters['bing_result']
        ciceron_result= parameters['ciceron_result']
        papago_result= parameters['papago_result']
        
        is_ok, new_id = voteTranslationResultObj.write(source_lang, target_lang,
                                                       original_text, google_result, bing_result, ciceron_result, papago_result)
        if is_ok == True:
            g.db.commit()
            return make_response(flaskjson.jsonify(new_id=new_id), 200)

        else:
            g.db.rollback()
            return make_response("Fail", 410)


    def translatorVote(self):
        voteTranslationResultObj = VoteTranslationResult(g.db)
        parameters = ciceron_lib.parse_request(request)

        result_id = parameters['result_id']
        versus = parameters['versus']
        vote_to = parameters['vote_to']

        is_ok = voteTranslationResultObj.vote(result_id, versus, vote_to)
        if is_ok == True:
            g.db.commit()
            return make_response("OK", 200)
        else:
            g.db.rollback()
            return make_response("Fail", 410)


if __name__ == '__main__':
    translator = Translator()
    requests = """논문의 평균 분량은 분야마다 다 다르다. 수학 같은 경우는 정말 A4용지 반 장 분량(…)의 논문이라고 하더라도 그 내용이 어떠한가에 따라서 세계를 발칵 뒤집는 불후의 논문이 될 수도 있다.[2] 사회과학은 그보다는 좀 더 길어진다. 대개의 심리학 논문은 20~30장 선에서 어지간하면 글이 끝나고, 정치학은 비슷하거나 그보다는 좀 더 긴 편이다. 논문의 방대함으로는 (연구주제에 따라서는) 행정학이 유명한데, 이 분야는 나랏님 하시는 일을 다루는지라 일단 데이터 양부터가 장난이 아니다. 오죽하면 행정학자들끼리 "우리는 학회를 한번 갔다오면 왜 연구실에 전화번호부 두께의 학회지가 너댓 편씩 쌓이지?"(…) 같은 농담을 주고받을 정도이니...[3] 그 외에도 논문 분량이 당연히 백여 페이지를 한참 넘을 것으로 기대되는 분야들은 꽤 있다. 단, 학술지 논문에 비해 우리 위키러들이 정말로 궁금할 학위논문의 경우 분량이 그 5~10배 가량 육박하는 경우가 많으니 참고. 일부 박사논문은 납본되는 걸 보면 정말로 책 한 권이 나온다.(...)  좀 심하게 말하면, 어떤 학술적인 글을 쓰는데 분량을 신경쓰는 것은 레포트 쓰는 학부생들의 수준에서 바라보는 시각일 수 있다. (굳이 좋게 평하자면, 최소한의 논문다운 논문을 쓰기 위한 휴리스틱이다.) 학계에서 논문의 가치는 그 논문의 양이 얼마나 방대한지는 전혀 상관없다. 일부 사회과학 분야 논문들은 가설을 한번에 30개 이상씩(!) 검증하기도 하나, 그런 논문이 가설 하나 검증하는 논문, 아니 아무도 신경쓰지 않은 문제를 최초로 제기하느라 가설은 아예 검증하지도 못하고 제안하기만 한 논문보다 우월하다고 취급되지는 않는다. 가설을 많이 검증한다고 해도 그 검증과정이나 논리적 차원에서 결함이나 비약이 있다면 가차없이 탈탈 털릴 뿐이다. 원론적으로, 인문학이나 예술분야라고 해도 자신의 독창적 생각을 타인에게 설득력 있게 전달하는 과정이 중요하게 취급되는 것은 당연하다.  공연히 분량을 늘린답시고 논문에서 논거를 질질 끌거나 쓸데없는 데이터를 넣거나 하면 당연히 또 탈탈 털린다. 애초에 학계라는 곳은 타인의 언급을 인용하는 것조차도 논리적 전개에 불필요해 보인다 싶으면 가차없이 불벼락을 내리는 바닥이다.[4] 필요한 말을 안 써서 까이기도 하지만, 쓸데없는 말이 너무 많다고 까이기도 하니, 논문을 준비하는 연구자는 이래저래 피곤하다. 게다가 교수들도 긴 글 읽기는 싫어하는 경우가 많다.(…)[5] """
    is_ok, result = translator.doWork(1, 2, requests)
    print (result)
