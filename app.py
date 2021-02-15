#!/usr/bin/env python
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_caching import Cache
from requests import Session
from datasnap import DatasnapSessionAdapter
from typing import Dict, Any
import re
app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
CORS(app)


@app.route('/')
def index():
    return jsonify({"test": get_server_ip()})


def get_server_ip():
    session = get_session()
    r = session.get(
        'http://servidor.shsistemas.net:7077/datasnap/rest/TSM/GetIPAcessoRemoto/CAAND')
    m = re.match(r'ok(.*)', r.json()['result'][0])
    return m.group(1)


def get_session():
    session = getattr(g, 'session', None)
    if session is None:
        session = Session()
        session.mount('http://', DatasnapSessionAdapter(cache))
        session.mount('https://', DatasnapSessionAdapter(cache))
        session.hooks['response'].append(
            lambda r, *args, **kwargs: r.raise_for_status())
        g.session = session
    return session


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
