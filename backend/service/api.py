from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import json
from flask import Blueprint, jsonify, render_template
from werkzeug.exceptions import HTTPException

from service.config import config



import datetime


api = Blueprint('api', __name__)

v = '/v1/'

@api.route(v+'register')
def register():
    return render_template('register.html')


@api.route(v+'poke', methods=['POST'])
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
