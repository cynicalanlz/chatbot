from __future__ import print_function
import httplib2
import os
import datetime


from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow

import json
from flask import Blueprint, jsonify, render_template,redirect
from werkzeug.exceptions import HTTPException

from service.config import config, google_config

api = Blueprint('api', __name__)
base = Blueprint('base', __name__)

v = '/v1/'



@api.route(v+'register')
def register():

    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')


    store = Storage(credential_path)
    credentials = store.get()

    if not credentials or credentials.invalid:
        flow = OAuth2WebServerFlow(
            **google_config, redirect_uri_path='/api/v1/register_cb')        
        auth_uri = flow.step1_get_authorize_url()


    return  redirect(auth_uri, code=302)


@api.route(v+'register_cb')
def register_cb():

    code = request.args.get('code')

    print(code)

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
