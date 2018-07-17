# -*- coding: utf-8 -*-
from flask import Blueprint
import app.users.controllers as ctrl

users = Blueprint('users', __name__)

# @app.route('/api/v1/setAuthCode', methods=['POST'])
users.add_url_rule('/setAuthCode', view_func=ctrl.setAuthCode, methods=['POST'])
# users.add_url_rule('/set', view_func=ctrl.setAuthCode, methods=['POST'])

# @app.route('/api/v1/checkAuthCode', methods=['POST'])
users.add_url_rule('/checkAuthCode', view_func=ctrl.checkAuthCode, methods=['POST'])
# users.add_url_rule('/check', view_func=ctrl.checkAuthCode, methods=['POST'])


# @app.route('/api/v1/getId', methods=['POST'])
users.add_url_rule('/getId', view_func=ctrl.getId, methods=['POST'])
# users.add_url_rule('/', view_func=ctrl.getId, methods=['POST'])


# @app.route('/api/v1/setLanguage', methods=['POST'])
users.add_url_rule('/setLanguage', view_func=ctrl.setLanguage, methods=['POST'])
# users.add_url_rule('/languages', view_func=ctrl.setLanguage, methods=['POST'])

# @app.route('/api/v1/setSourceLanguage', methods=['POST'])
users.add_url_rule('/setSourceLanguage', view_func=ctrl.setSourceLanguage, methods=['POST'])
# users.add_url_rule('/languages/source', view_func=ctrl.setSourceLanguage, methods=['POST'])

# @app.route('/api/v1/setTargetLanguage', methods=['POST'])
users.add_url_rule('/setTargetLanguage', view_func=ctrl.setTargetLanguage, methods=['POST'])
# users.add_url_rule('/languages/target', view_func=ctrl.setTargetLanguage, methods=['POST'])


# @app.route('/api/v1/clearLastSentence', methods=['POST'])
users.add_url_rule('/clearLastSentence', view_func=ctrl.clearLastSentence, methods=['DELETE'])
# users.add_url_rule('/sentence', view_func=ctrl.clearLastSentence, methods=['DELETE'])


# @app.route('/api/v1/actionLog', methods=['GET'])
users.add_url_rule('/actionLog', view_func=ctrl.actionLog, methods=['GET'])
