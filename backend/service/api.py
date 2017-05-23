import json
from flask import Blueprint, jsonify
from werkzeug.exceptions import HTTPException

from service.config import config


api = Blueprint('api', __name__)


@api.route('/v1/hello')
def hello():
    return jsonify("Hello World!")


@api.route('/v1/poke', methods=['POST'])
def poke():
    response = {
        'msg': 'Ouch!',
        'status': 'SUCCESS'
        }

    return jsonify(response)


@api.route('/version')
def version():
    with open('version.json') as fp:
        version = json.load(fp)

    return jsonify(version)


@api.route('/health')
def health():
    response = {
        'health': 'ENABLED'
    }

    return jsonify(response), 200
