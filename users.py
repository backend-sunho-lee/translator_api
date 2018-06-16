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
                  , "point": 0
                    }

        else:
            return {
                    "is_new": False
                  , "user_id": ret['id']
                  , "eos_id": ret['eos_id']
                  , "media": ret['media']
                  , "text_id": ret['text_id']
                  , "languages": ret['languages']
                  , "point": ret['point']
                    }

    def getPoint(self, conn, media, text_id, point):
        cursor = conn.cursor()
        query = """
            UPDATE users
            SET point = point + %s
            WHERE media = %s AND text_id = %s
        """
        try:
            cursor.execute(query, (point, media, text_id, ))
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

