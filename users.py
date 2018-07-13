import traceback

class Users(object):
    def _getId(self, conn, media, id_external, text_id=None):
        cursor = conn.cursor()

        if media == 'mycat':
            if id_external and text_id is None:
                email = id_external
            else:
                email = text_id
            query = """SELECT u.id, ru.text_id, eos_id, 'mycat' as media, languages, source_lang, target_lang, chat_id, last_original_text_id, point, id_external
                       FROM real_users ru JOIN users u ON u.real_user_id = ru.id WHERE ru.text_id=%s;"""
            cursor.execute(query, (email, ))
            ret = cursor.fetchone()
            return ret

        # Will be activated
        query = """
            SELECT * FROM users
            WHERE 
                  media = %s
              AND id_external = %s
        """

        #query = """
        #    SELECT * FROM users
        #    WHERE 
        #          media = %s
        #      AND text_id = %s
        #"""
        cursor.execute(query, (media, id_external, ))
        ret = cursor.fetchone()
        if ret is None or len(ret) < 1:
            return None

        # Will be deleted later
        #query_update = """
        #    UPDATE users
        #    SET id_external = %s
        #    WHERE
        #          media = %s
        #      AND text_id = %s
        #"""
        #cursor.execute(query_update, (id_external, media, text_id, ))
        #conn.commit()

        return ret

    def _setId(self, conn, media, id_external, text_id=None):
        cursor = conn.cursor()
        query = """
            INSERT INTO users
              (media, text_id, point, created_at, id_external)
            VALUES
              (%s, %s, 0, CURRENT_TIMESTAMP, %s)
        """
        try:
            cursor.execute(query, (media, text_id, id_external, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False, None

        conn.commit()

        query_getId = "SELECT LAST_INSERT_ID() as last_id"
        cursor.execute(query_getId)
        ret = cursor.fetchone()
        if ret is None or len(ret) < 1:
            return False, None

        return True, ret['last_id']

    def _getPoint(self, conn, user_id):
        cursor = conn.cursor()
        query = """
            SELECT * FROM points
            WHERE user_id = %s
        """
        cursor.execute(query, (user_id, ))
        ret = cursor.fetchall()
        return ret

    def getId(self, conn, media, id_external, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        if ret is None or len(ret) < 1:
            is_ok, user_id = self._setId(conn, media, id_external, text_id)
            return {
                    "is_new": True
                  , "user_id": user_id
                  , "eos_id": None
                  , "media": media
                  , "text_id": text_id
                  , "languages": ""
                  , "source_lang": None
                  , "target_lang": None
                  , "last_original_text_id": None
                  , "chat_id": None
                  , "point": []
                  , 'id_external': None
                    }

        else:
            return {
                    "is_new": False
                  , "user_id": ret['id']
                  , "eos_id": ret['eos_id']
                  , "media": ret['media']
                  , "text_id": ret['text_id']
                  , "languages": ret.get('languages', None)
                  , "source_lang": ret.get('source_lang', None)
                  , "target_lang": ret.get('target_lang', None)
                  , "chat_id": ret.get('chat_id', None)
                  , "last_original_text_id": ret.get('last_original_text_id', None)
                  , "point": self._getPoint(conn, ret['id'])
                  , "id_external": ret.get('id_external', None)
                    }

    def getPoint(self, conn, media, id_external, source_lang, target_lang, point, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        cursor = conn.cursor()
        user_obj = self.getId(conn, media, id_external, text_id)
        query = """
            INSERT INTO points
              (user_id, source_lang, target_lang, point)
            VALUES
              (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE point = point + %s
        """
        try:
            cursor.execute(query, (user_obj['user_id'], source_lang, target_lang, point, point, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True


    def setLanguage(self, conn, media, id_external, languages, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET languages = %s,
                  text_id = %s
            WHERE media = %s
              AND id_external = %s
        """
        
        try:
            cursor.execute(query, (languages, text_id, media, id_external, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

    def setSourceLanguage(self, conn, media, id_external, source_lang, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET source_lang = %s,
                  text_id = %s
            WHERE media = %s
              AND id_external = %s
        """
        
        try:
            cursor.execute(query, (source_lang, text_id, media, id_external, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

    def setTargetLanguage(self, conn, media, id_external, target_lang, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET target_lang = %s,
                  text_id = %s
            WHERE media = %s
              AND id_external = %s
        """
        
        try:
            cursor.execute(query, (target_lang, text_id, media, id_external, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

    def setChatId(self, conn, media, id_external, chat_id, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET chat_id = %s,
                  text_id = %s
            WHERE media = %s
              AND id_external = %s
        """
        
        try:
            cursor.execute(query, (chat_id, text_id, media, id_external, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

    def setAuthCode(self, conn, media, id_external, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        from random import randint

        code = randint(100000, 999999)
        user_obj = self._getId(conn, media, id_external, text_id)
        chat_id = user_obj.get('chat_id')
        if chat_id == None:
            return False, None, None

        cursor = conn.cursor()
        query = """
            INSERT INTO auth_code
              (user_id, auth_code, is_used, requested_at)
            VALUES
              (%s,      %s,        false,   CURRENT_TIMESTAMP)
        """
        try:
            cursor.execute(query, (user_obj['id'], str(code), ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False, None, None

        conn.commit()
        return True, code, chat_id

    def checkAuthCode(self, conn, media, id_external, code, text_id=None):
        ret = self._getId(conn, media, id_external, text_id)
        user_obj = self._getId(conn, media, id_external, text_id)
        chat_id = user_obj['chat_id']
        cursor = conn.cursor()
        query_check = """
            SELECT id, auth_code
            FROM auth_code
            WHERE user_id = %s AND is_used = false
            ORDER BY requested_at DESC
            LIMIT 1
        """
        cursor.execute(query_check, (user_obj['id'], ))
        ret = cursor.fetchone()
        if ret is None or len(ret) < 1:
            return False, chat_id

        rec_id = ret['id']
        code_fromDb = ret['auth_code']
        if code_fromDb != code:
            return False, chat_id

        query_mark = """
            UPDATE auth_code
            SET is_used = true
            WHERE id = %s
        """

        try:
            cursor.execute(query_mark, (rec_id, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False, chat_id

        conn.commit()
        return True, chat_id

