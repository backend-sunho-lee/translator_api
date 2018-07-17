# -*- coding: utf-8 -*-
from flask import Blueprint
import app.translator.controllers as ctrl

translator = Blueprint('translator', __name__)

# @app.route('/api/v2/internal/translate', methods=['POST'])
translator.add_url_rule('/v2/internal/translate', view_func=ctrl.translateInternal, methods=['POST'])
# translator.add_url_rule('/internal', view_func=ctrl.translateInternal, methods=['POST'])

# @app.route('/api/v2/external/translate', methods=['POST'])
translator.add_url_rule('/v2/external/translate', view_func=ctrl.translateExternal, methods=['POST'])
# translator.add_url_rule('/external', view_func=ctrl.translateExternal, methods=['POST'])


# @app.route('/api/v1/completePairLog', methods=['GET'])
translator.add_url_rule('/v1/completePairLog', view_func=ctrl.completePariLog, methods=['GET'])
# translator.add_url_rule('/', view_func=ctrl.completePariLog, methods=['GET'])

# @app.route('/api/v1/getSentence', methods=['GET'])
translator.add_url_rule('/v1/getSentence', view_func=ctrl.getSentence, methods=['GET'])
# translator.add_url_rule('/sentence', view_func=ctrl.getSentence, methods=['GET'])


# @app.route('/api/v1/inputTranslation', methods=['POST'])
translator.add_url_rule('/v1/inputTranslation', view_func=ctrl.inputTranslation, methods=['POST'])
# translator.add_url_rule('/telegram', view_func=ctrl.inputTranslation, methods=['POST'])

# @app.route('/api/v1/translation/mycat', methods=['POST'])
translator.add_url_rule('/v1/translation/mycat', view_func=ctrl.inputTranslation_from_mycat, methods=['POST'])
# translator.add_url_rule('/mycat', view_func=ctrl.inputTranslation_from_mycat, methods=['POST'])
