import unittest
import json
from unittest.mock import patch

from detourserver import app

with open('./config.json', 'r') as f:
    config = json.load(f)
CICERON_API_KEY = config['ciceron']['translator']

class DetourserverTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_internal_translate(self):
        with app.app_context():
            res = self.app.post('/api/v2/internal/translate',
                                data=dict(
                                    sentence= 'One-way, or round-trip?',
                                    source_lang= 'en',
                                    target_lang= 'ko',
                                    tags= 'mycat,sunny,test',
                                    media= 'mycat',
                                    order_user= 'sunny@ciceron.me',
                                    where_contribute= 'mycat',
                                    memo= 'sunny, testing.'
                                ),
                                headers={"Authorization": CICERON_API_KEY})
        self.assertEqual(res.status_code, 200)

    def test_external_translate(self):
        with app.app_context():
            res = self.app.post('/api/v2/external/translate',
                                data=dict(
                                    sentence= "I'd like to book a flight to New York.",
                                    source_lang= 'en',
                                    target_lang= 'ko',
                                    tags= 'mycat,sunny,test',
                                    media= 'mycat',
                                    order_user= 'sunny@ciceron.me',
                                    where_contribute= 'mycat',
                                    memo= 'sunny, testing.'
                                ),
                                headers={"Authorization": CICERON_API_KEY})
        self.assertEqual(res.status_code, 200)

    def test_logout(self):
        with app.app_context():
            res = self.app.get('/api/v1/logout')
        self.assertEqual(res.status_code, 200)

    def test_get_id(self):
        with app.app_context():
            res = self.app.post('/api/v1/getId',
                                data=dict(
                                    media = 'telegram',
                                    id_external = 604252092,
                                    text_id = 'ooohnus',
                                    chat_id = '604252092'
                                ))
        self.assertEqual(res.status_code, 200)

    def test_set_language(self):
        with app.app_context():
            res = self.app.post('/api/v1/setLanguage',
                                data=dict(
                                    media = 'telegram',
                                    id_external = 604252092,
                                    text_id = 'ooohnus',
                                    languages = 'en,ko'
                                ))
        self.assertEqual(res.status_code, 200)

    def test_set_source_language(self):
        with app.app_context():
            res = self.app.post('/api/v1/setSourceLanguage',
                                data=dict(
                                    media = 'telegram',
                                    id_external = 604252092,
                                    text_id = 'ooohnus',
                                    language = 'en'
                                ))
        self.assertEqual(res.status_code, 200)

    def test_set_target_language(self):
        with app.app_context():
            res = self.app.post('/api/v1/setTargetLanguage',
                                data=dict(
                                    media = 'telegram',
                                    id_external = 604252092,
                                    text_id = 'ooohnus',
                                    language = 'ko'
                                ))
        self.assertEqual(res.status_code, 200)

    def test_clear_last_sentence(self):
        with app.app_context():
            res = self.app.post('/api/v1/clearLastSentence',
                                data=dict(
                                    media = 'telegram',
                                    id_external = 604252092,
                                    text_id = 'ooohnus'
                                ))
        self.assertEqual(res.status_code, 200)

    def test_get_sentece(self):
        with app.app_context():
            res = self.app.get('/api/v1/getSentence',
                               query_string=dict(
                                   languages = 'en',
                                   target_lang = 'ko',
                                   media = 'telegram',
                                   id_external = 604252092,
                                   text_id = 'ooohnus'
                               ))
        self.assertEqual(res.status_code, 200)

    def test_input_translation(self):
        with app.app_context():
            res = self.app.post('/api/v1/inputTranslation',
                               data=dict(
                                   contributor_external_id=604252092,
                                   original_text_id = 3,
                                   contributor_media = 'telegram',
                                   contributor_text_id = 'sunny@ciceron.me',
                                   tags = 'test,sunny',
                                   target_lang = 'ko',
                                   target_text = '아름다운 날이에요',
                                   where_contribute = 'telegram',
                               ))
        self.assertEqual(res.status_code, 200)

    def test_input_translation_mycat(self):
        with app.app_context():
            res = self.app.post('/api/v1/translation/mycat',
                               data=dict(
                                   original_text_id = 3,
                                   contributor_media = 'mycat',
                                   contributor_text_id = 'sunny@ciceron.me',
                                   tags = 'mycat,test,sunny',
                                   target_lang = 'ko',
                                   target_text = '아름다운 날이에요',
                                   where_contribute = 'mycat'
                               ))
        self.assertEqual(res.status_code, 200)

    def test_complete_pairlog(self):
        with app.app_context():
            res = self.app.get('/api/v1/completePairLog')
        self.assertEqual(res.status_code, 200)

    def test_action_log(self):
        with app.app_context():
            res = self.app.get('/api/v1/actionLog')
        self.assertEqual(res.status_code, 200)

    def test_set_auth_code(self):
        with app.app_context():
            res = self.app.post('/api/v1/setAuthCode',
                                data=dict(
                                    media = 'telegram',
                                    id_external = 212244247,
                                    text_id = 'psy2848048'
                                ))
        self.assertEqual(res.status_code, 200)

    @patch('users.Users.checkAuthCode', return_value=(True, 212244247))
    def test_check_auth_code(self, return_value):
        with app.app_context():
            res = self.app.post('/api/v1/checkAuthCode',
                                data=dict(
                                    media = 'telegram',
                                    id_external = 212244247,
                                    text_id = 'psy2848048',
                                    code = '637006'
                                ))
        self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
