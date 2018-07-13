import traceback
import pymysql

class Sentences(object):
    def _getOriginSentenceInfo(self, conn, origin_text_id):
        cursor = conn.cursor()
        query = """
            SELECT * FROM origin_text_users
            WHERE id = %s
            LIMIT 1
        """
        cursor.execute(query, (origin_text_id, ))
        return cursor.fetchone()

    def _getTargetSentenceInfo(self, conn, target_text_id):
        cursor = conn.cursor()
        query = """
            SELECT * FROM target_text_users
            WHERE id = %s
            LIMIT 1
        """
        cursor.execute(query, (origin_text_id, ))
        return cursor.fetchone()

    def _inputOriginalSentence(self, conn, contributor_id, language,
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

    def _inputTargetSentence(self, conn, contributor_id, original_text_id, language,
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

    def _inputCompleteSentence(self, conn, 
            origin_text_id, target_text_id, 
            origin_contributor_id, target_contributor_id, 
            origin_lang, target_lang,
            origin_text, target_text,
            origin_tags, target_tags,
            origin_where_contributed, target_where_contributed):
        cursor = conn.cursor()
        query = """
            INSERT INTO complete_sentence
              (origin_text_id, target_text_id, 
               origin_contributor_id, target_contributor_id, 
               origin_lang, target_lang,
               hash_origin, hash_target,
               origin_text, target_text,
               origin_tags, target_tags,
               origin_where_contributed, target_where_contributed,
               added_at, cnt)

            VALUES
              (%s, %s,
               %s, %s, 
               %s, %s,
               MD5(%s), MD5(%s),
               %s, %s,
               %s, %s,
               %s, %s,
               CURRENT_TIMESTAMP, 0)
        """
        try:
            cursor.execute(query, (
                origin_text_id, target_text_id, 
                origin_contributor_id, target_contributor_id, 
                origin_lang, target_lang,
                origin_text, target_text,
                origin_text, target_text,
                origin_tags, target_tags,
                origin_where_contributed, target_where_contributed, ))

        except pymysql.err.IntegrityError:
            print("Duplicate sentence {}".format(target_text))
            return 1, None

        except:
            traceback.print_exc()
            conn.rollback()
            return 2, None

        query_getId = "SELECT LAST_INSERT_ID() as last_id"
        cursor.execute(query_getId)
        ret = cursor.fetchone()
        if ret is None or len(ret) < 1:
            return 3, None

        return 0, ret['last_id']

    def _markAsTranslated(self, conn, origin_text_id):
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

    def clearLastSentenceId(self, conn, media, id_external, text_id=None):
        cursor = conn.cursor()

        query_updateId = """
            UPDATE users
              SET last_original_text_id = %s,
                  text_id = %s,
                  last_connected_time = CURRENT_TIMESTAMP 
            WHERE media = %s AND id_external = %s
        """
        try:
            cursor.execute(query_updateId, (None, text_id, media, id_external, ))
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()
        return True


    def getOneSentences(self, conn, media, id_external, language, text_id=None):
        cursor = conn.cursor()
        query = """
            SELECT * FROM origin_text_users
            WHERE language = %s
              AND is_translated = false
            ORDER BY contributed_at DESC
            LIMIT 1
        """
        cursor.execute(query, (language, ))
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

    def inputTranslation(self, conn,
            original_text_id,
            target_contributor_id, target_text, target_lang,
            where_contribute,
            tags=""):
        is_ok, target_text_id = self._inputTargetSentence(conn, target_contributor_id, original_text_id, target_lang, target_text, where_contribute, tags)

        ret = self._getOriginSentenceInfo(conn, original_text_id)
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

        is_ok = self._markAsTranslated(conn, original_text_id)

        #code, complete_id = self._inputCompleteSentence(conn,
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

