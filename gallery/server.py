import os

from flask import Flask, jsonify, make_response

app = Flask(__name__)

@app.route('/')
def index():
    with open('gallery/index.html') as fp:
        return fp.read()

@app.route('/static/<filename>')
def load_static(filename):
    with open('gallery/static/%s' % (filename,)) as fp:
        if filename.endswith('.css'):
            resp = make_response(fp.read())
            resp.headers['Content-Type'] = 'text/css'

            return resp
        return fp.read()

@app.route('/maps')
def list_maps():
    return jsonify( [f for f in os.listdir('gallery/maps') if f.endswith('.svg')] )

@app.route('/maps/<name>')
def get_map(name):
    with open('gallery/maps/%s' % (name,)) as fp:
        return fp.read()

if __name__ == '__main__':
    print('Starting map server...')
    app.run()