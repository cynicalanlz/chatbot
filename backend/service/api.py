from __future__ import print_function
import httplib2
import os
import datetime
import yajl as json

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow, Credentials

import httplib2
import shortuuid

from flask import Blueprint, jsonify, render_template,redirect, request, make_response
from werkzeug.exceptions import HTTPException

from service.config import config, google_config
from service.user.models import User
from service.shared.models import db
from service.utils.lib import get_or_create
from service.utils.calendar import get_service, get_events, create_event

api = Blueprint('api', __name__)


v = '/v1/'

def events_resp(creds, usr):
    """
    Lists authorized user events
    """
    service = get_service(creds)
    events = get_events(service)
    return make_response(
        render_template(
            'registered.html',
            name=usr.id,
            events=events,
        ))


@api.route(v+'register_cb')
def register_google():

    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
        
    uid = request.cookies.get("id") or shortuuid.ShortUUID().random(length=22)
    code = request.args.get('code')
    slid = request.args.get('slid')

    if not slid and not code:
        return jsonify({
            'msg' : 'Slid or code not set'
            })


    usr, created = get_or_create(db.session, User, default_values={'slid' : slid }, id=uid)

    if not created and usr.slid == None:
        usr.slid = slid
        db.session.commit()

    if usr.google_auth:
        creds = Credentials.new_from_json(json.loads(usr.google_auth))
        if creds and not creds.invalid:
            resp = events_resp(creds, usr)
            return resp
 
    flow = OAuth2WebServerFlow(**google_config)    

    if not code:            
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri, code=302)

    creds = flow.step2_exchange(code)
    creds_json = creds.to_json()  
    usr.google_auth = json.dumps(creds.to_json())
    db.session.commit()
    resp = events_resp(creds, usr)
    resp.set_cookie('id', uid )

    return resp


@api.route(v+'register_js')
def register_js():
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


