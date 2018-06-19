import traceback

class Users(object):
    def _getId(self, conn, media, text_id):
        cursor = conn.cursor()
        query = """
            SELECT * FROM users
            WHERE 
                  media = %s
              AND text_id = %s
        """
        cursor.execute(query, (media, text_id, ))
        return cursor.fetchone()

    def _setId(self, conn, media, text_id):
        cursor = conn.cursor()
        query = """
            INSERT INTO users
              (media, text_id, point, created_at)
            VALUES
              (%s, %s, 0, CURRENT_TIMESTAMP)
        """
        try:
            cursor.execute(query, (media, text_id, ))
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

    def getId(self, conn, media, text_id):
        ret = self._getId(conn, media, text_id)
        if ret is None or len(ret) < 1:
            is_ok, user_id = self._setId(conn, media, text_id)
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
                    }

        else:
            return {
                    "is_new": False
                  , "user_id": ret['id']
                  , "eos_id": ret['eos_id']
                  , "media": ret['media']
                  , "text_id": ret['text_id']
                  , "languages": ret['languages']
                  , "source_lang": ret['source_lang']
                  , "target_lang": ret['target_lang']
                  , "chat_id": ret['chat_id']
                  , "last_original_text_id": ret['last_original_text_id']
                  , "point": self._getPoint(conn, ret['id'])
                    }

    def getPoint(self, conn, media, text_id, source_lang, target_lang, point):
        cursor = conn.cursor()
        user_obj = self.getId(conn, media, text_id)
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


    def setLanguage(self, conn, media, text_id, languages):
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET languages = %s
            WHERE media = %s
              AND text_id = %s
        """
        
        try:
            cursor.execute(query, (languages, media, text_id, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

    def setSourceLanguage(self, conn, media, text_id, source_lang):
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET source_lang = %s
            WHERE media = %s
              AND text_id = %s
        """
        
        try:
            cursor.execute(query, (source_lang, media, text_id, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

    def setTargetLanguage(self, conn, media, text_id, target_lang):
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET target_lang = %s
            WHERE media = %s
              AND text_id = %s
        """
        
        try:
            cursor.execute(query, (target_lang, media, text_id, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

    def setChatId(self, conn, media, text_id, chat_id):
        cursor = conn.cursor()
        query = """
            UPDATE users
              SET chat_id = %s
            WHERE media = %s
              AND text_id = %s
        """
        
        try:
            cursor.execute(query, (chat_id, media, text_id, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True

