import traceback

class Sentences(object):
    def _getOriginSentenceInfo(self, conn, origin_text_id):
        cursor = conn.cursor()
        query = """
            SELECT * FROM origin_texts
            WHERE id = %s
            LIMIT 1
        """
        cursor.execute(query, (origin_text_id, ))
        return cursor.fetchone()

    def _getTargetSentenceInfo(self, conn, target_text_id):
        cursor = conn.cursor()
        query = """
            SELECT * FROM target_texts
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
        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()

        query_getId = "SELECT LAST_INSERT_ID() as last_id"
        cursor.execute(query_getId)
        ret = cursor.fetchone()
        if ret is None or len(ret) < 1:
            return False, None

        return True, ret['last_id']

    def _inputTargetSentence(self, conn, contributor_id, original_text_id, language,
            text, where_contributed, tags=""):
        cursor = conn.cursor()
        query = """
            INSERT INTO target_texts
              (contributor_id, 
              origin_text_id, 
              language,
              text, 
              confirm_cnt,
              tag, 
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

    def _inputCompleteSentence(self, conn, 
            origin_text_id, target_text_id, 
            origin_contributor_id, target_contributor_id, 
            origin_lang, target_lang,
            hash_origin, hash_target,
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

        except:
            traceback.print_exc()
            conn.rollback()
            return False

        conn.commit()

        query_getId = "SELECT LAST_INSERT_ID() as last_id"
        cursor.execute(query_getId)
        ret = cursor.fetchone()
        if ret is None or len(ret) < 1:
            return False, None

        return True, ret['last_id']

    def _markAsTranslated(self, origin_text_id):
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

        conn.commit()
        return True


    def getOneSentences(self, conn, languages):
        cursor = conn.cursor()
        splited_languages = [ "'{}'".format( item.strip() ) for item in languages.split(',') ]
        organized_languages = ', '.join(splited_languages)
        query = """
            SELECT * FROM origin_texts
            WHERE is_translated = false
              AND language IN (%s)
            LIMIT 1
        """
        cursor.execute(query, (organized_languages, ))
        return cursor.fetchone()

    def inputTranslation(self, conn,
            original_text_id,
            target_contributor_id, target_text, target_lang,
            where_contribute
            tags=""):
        is_ok, target_text_id = self._inputTargetSentence(conn, target_contributor_id, original_text_id, target_lang, target_text, where_contribute, tags)

        ret = self._getOriginSentenceInfo(origin_text_id)
        if ret is None or len(ret) < 1:
            return False

        original_contributor_id = ret['contributor_id']
        origin_lang = ret['language']
        origin_text = ret['text']
        origin_tag = ret['tag']
        origin_where_contributed = ret['where_contribute']

        is_ok = self._markAsTranslated(original_text_id)

        is_ok, complete_id = self._inputCompleteSentence(conn,
                origin_text_id, target_text_id,
                origin_contributor_id, target_contributor_id,
                origin_lang, target_lang,
                origin_text, target_text,
                origin_tag, tags,
                origin_where_contributed, where_contribute)

        return True, complete_id

