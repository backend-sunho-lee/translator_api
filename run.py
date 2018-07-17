# -*- coding: utf-8 -*-
from app import app
from gevent.wsgi import WSGIServer

http_server = WSGIServer(('0.0.0.0', 5000), app)
http_server.serve_forever()
