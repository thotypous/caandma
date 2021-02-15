#!/usr/bin/env python
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_caching import Cache
from flask_cachecontrol import FlaskCacheControl, cache as cache_control
from requests import Session
from datasnap import DatasnapSessionAdapter
from adbs import TableDeserializer
from io import BytesIO
from zlib import decompress
from base64 import b64decode
import os
import re
app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
flask_cache_control = FlaskCacheControl()
flask_cache_control.init_app(app)
CORS(app)


@app.route('/server_ip')
@cache_control(max_age=300, public=True)
def server_ip():
    return jsonify(get_server_ip())


@app.route('/status_loja')
@cache_control(max_age=60, public=True)
def status_loja():
    session = get_session()
    r = session.get('{}/GetStatusLoja/'.format(get_base_url()))
    return jsonify(r.json()['result'][0])


@app.route('/departamentos')
@cache_control(max_age=1800, public=True)
@cache.cached(timeout=1800)
def departamentos():
    return table_req('/GetDepartamentos/PedMoveis.2017/')


@app.route('/produtos_dept/<int:dept>')
def produtos_dept(dept):
    return table_req('/GetProdutosDept/PedMoveis.2017/{}/'.format(dept))


@app.route('/produtos_consulta/<string:q>')
def produtos_consulta(q):
    return table_req('/GetProdutosConsulta/PedMoveis.2017/{}/'.format(q))


@app.route('/produtos/<string:q>')
def produtos(q):
    return table_req('/GetProdutos/PedMoveis.2017/{}/'.format(q))


def get_base_url():
    server_ip = get_server_ip()
    return 'http://{}:5362/datasnap/rest/TsmPedidosMoveis'.format(server_ip)


def table_req(path):
    session = get_session()
    r = session.get(
        '{}{}'.format(get_base_url(), path))
    return jsonify(table_des(r.json()))


def table_des(json):
    fvalue = (json['result'][0]['fields']['FDataSets']['fields']
              ['FMembers'][0]['fields']['FJsonValue']['fields']['FValue'])
    f = BytesIO(decompress(b64decode(fvalue)))
    return TableDeserializer(f).load()


@cache.cached(timeout=300, key_prefix='server_ip')
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
        session.auth = (os.getenv('DATASNAP_USER', ''),
                        os.getenv('DATASNAP_PASS', ''))
        g.session = session
    return session


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
