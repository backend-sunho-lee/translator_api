# -*- coding: utf-8 -*-
from flask import Flask, make_response, jsonify, session
from flask_session import Session
from flask_cors import CORS
from flask_caching import Cache
import json as pyjson
import pymysql

conf = {}
with open('./config.json', 'r') as f:
    conf = pyjson.load(f)

DATABASE = conf['db']

VERSION = '1.1'
DEBUG = True
GCM_API_KEY = conf['google']['key']
BING_KEY = conf['bing']['key']
SESSION_TYPE = 'redis'
SESSION_COOKIE_NAME = "cicerontranslator"
BOT_API_KEY = conf['telegram']['trainer']

app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = conf['app']['secret_key']
app.project_number = conf['google']['project_id']

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
Session(app)
cors = CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": "true"}})


def connect_db():
    return pymysql.connect(host=DATABASE['host'],
                           user=DATABASE['user'],
                           password=DATABASE['password'],
                           db=DATABASE['db'],
                           charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor)


# ##################################################### 모듈 연결 ###################################################### #

from app.users.urls import users
# app.register_blueprint(users, url_prefix='/api/v1/users')
app.register_blueprint(users, url_prefix='/api/v1')

from app.translator.urls import translator
# app.register_blueprint(translator, url_prefix='/api/v2/translator')
app.register_blueprint(translator, url_prefix='/api')

#: 등록된 url 확인하기
print(app.url_map)

########################################################################################################################

@app.before_request
def before_request():
    """
    모든 API 실행 전 실행하는 부분
    """
    # if request.url.startswith('http://'):
    #     url = request.url.replace('http://', 'https://', 1)
    #     code = 301
    #     return redirect(url, code=code)
    #
    # if '/api' in request.environ['PATH_INFO']:
    #     is_ok = common.ddos_check_and_write_log()
    #     if is_ok is False:
    #         error = {
    #             "code": 1301,
    #             "type": "Blocked",
    #             "message": "당신은 블랙리스트!"
    #         }
    #         return make_response(jsonify(error=error), 403)
    pass


@app.teardown_request
def teardown_request(exception):
    """
    모든 API 실행 후 실행하는 부분. 여기서는 DB 연결종료.
    """
    pass


@app.route('/')
def hello_world():
    return 'LangChain is working.'


@app.route('/api/v1/logout', methods=['GET'])
def logout():
    session['checked'] = False
    return make_response(jsonify(result="ok"), 200)

# #################################################### 에러 핸들링 ###################################################### #


@app.errorhandler(401)
def not_unauthorized(e):
    msg = e.description or "login required"
    error = {
        "code": 1000,
        "type": "Unauthorized",
        "message": msg
    }
    return make_response(jsonify(error=error), 401)


@app.errorhandler(403)
def forbidden(e):
    msg = e.description or "You don't have the permission to access the requested resource. " + \
          "It is either read-protected or not readable by the server."
    error = {
        "code": 1300,
        "type": "Forbidden",
        "message": msg
    }
    return make_response(jsonify(error=error), 403)


@app.errorhandler(400)
def not_unauthorized(e):
    msg = e.description or "Please check the required values(url, parameter, body) again with api documents."
    error = {
        "code": 2000,
        "type": "BadRequest",
        "message": msg
    }
    return make_response(jsonify(error=error), 400)


@app.errorhandler(404)
def not_found(e):
    msg = e.description or "The requested URL was not found on the server. " + \
          "If you entered the URL manually please check your spelling and try again."
    error = {
        "code": 2100,
        "type": "NotFound",
        "message": msg
    }
    return make_response(jsonify(error=error), 404)


@app.errorhandler(409)
def conflict(e):
    msg = e.description or \
          "The request could not be completed due to a conflict with the current state of the target resource." + \
          "This code is used in situations where the user might be able to resolve the conflict and resubmit the request."
    error = {
        "code": 2200,
        "type": "Conflict",
        "message": msg
    }
    return make_response(jsonify(error=error), 409)


@app.errorhandler(422)
def unprocessable_entity(e):
    msg = e.description or "The request was well-formed but was unable to be followed due to semantic errors."
    error = {
        "code": 2300,
        "type": "UnprocessableEntity",
        "message": msg
    }
    return make_response(jsonify(error=error), 422)


@app.errorhandler(503)
def service_unavailable(e):
    msg = "Server is temporary unavailable. " + e.description
    error = {
        "code": 2500,
        "type": "ServiceUnavailable",
        "message": msg
    }
    return make_response(jsonify(error=error), 503)
