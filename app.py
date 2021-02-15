#!/usr/bin/env python
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache
app = Flask(__name__)
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)
CORS(app)

@app.route('/')
def index():
    return jsonify({"test": "hi"})

if __name__ == '__main__':
    app.run(threaded=True, port=5000)
