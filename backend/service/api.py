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

from service.user.models import User, SlackTeam
from service.shared.models import db
from service.utils.lib import get_or_create
from service.utils.calendar import get_service, get_events, create_event

from slackclient import SlackClient


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
        ))


@api.route(v+'register_slack_team')
def register_slack_team():
    return render_template('register_slack.html')

def slack_team_process(token):
    h = httplib2.Http(".cache")
    format_string = config['SLACK_PROTOCOL']+"://"+config['SLACK_HOST']+"/api/v1/slack_team_process?token=%s"
    url = format_string % token
    (resp_headers, content) = h.request(url, "GET")
    return resp_headers

@api.route(v+"register_slack", methods=["GET", "POST"])
def post_install():
    # Retrieve the auth code from the request params
    auth_code = request.args['code']

    # An empty string is a valid token for this request
    sc = SlackClient("")

    # Request the auth tokens from Slack
    auth_response = sc.api_call(
        "oauth.access",
        client_id=config['SLACK_CLIENT_ID'],
        client_secret=config['SLACK_CLIENT_SECRET'],
        code=auth_code
    )

    tid = shortuuid.ShortUUID().random(length=22)

    team, created = get_or_create(
        db.session, 
        SlackTeam,
        default_values={'id' : tid },
        id=tid
        )    

    team.team_name = auth_response['team_name']
    team.team_id = auth_response['team_id']
    team.access_token = auth_response['access_token']
    team.bot_token = auth_response['bot']['bot_access_token']
    team.bot_user_id = auth_response['bot']['bot_user_id']
    db.session.commit()
    slack_team_process(team.bot_token)
  
    return jsonify({'msg' : 'ok'})


@api.route(v+'register_cb')
def register_google():

    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    returns page @@TODO: remove page and or redirect to slack.
    """
        
    code = request.args.get('code')
    tid = request.args.get('tid')
    slid = request.args.get('slid') or request.args.get('state')
    uid = request.cookies.get(tid) or str(shortuuid.ShortUUID().random(length=22))

    print(slid)


    if not slid and not code:
        return jsonify({
            'msg' : 'Slid or code not set'
            })

    usr, created = get_or_create(
        db.session, 
        User, 
        {   
            'slid' : slid, 
            'team_id' : tid,
            'id' : uid
        }, 
        slid=slid
    )

    print(usr.id)

    if usr.google_auth:
        creds = Credentials.new_from_json(json.loads(usr.google_auth))
        if creds and not creds.invalid:
            resp = events_resp(creds, usr)
            return resp    
 
    flow = OAuth2WebServerFlow(**google_config)    

    if not code and tid:            
        auth_uri = flow.step1_get_authorize_url(state=slid)
        redirect_response = make_response(redirect(auth_uri, code=302))
        redirect_response.set_cookie(tid, uid)
        return redirect_response

    creds = flow.step2_exchange(code)
    creds_json = creds.to_json() 

    usr.google_auth = json.dumps(creds.to_json())
    db.session.commit()

    resp = events_resp(creds, usr)

    return resp

@api.route(v+'get_tokens')
def get_tokens():

    # if request.remote_addr != '':
    #     return jsonify({})

    tokens = [x[0] for x in db.session.query(SlackTeam.bot_token).distinct()]
    response = {
        'tokens' : tokens
    }
    
    return jsonify(response), 200

@api.route(v+'get_user_google_auth')
def get_user_google_auth():
    slid = request.args.get('slid')
    text = db.session.query(User.google_auth).filter_by(slid=slid).first()
    response = {
        'google_auth' : text
    }
    return jsonify(response), 200


@api.route('/health')
def health():
    response = {
        'health': 'ENABLED'
    }

    return jsonify(response), 200


@api.route("/spec")
def spec():
    return jsonify(swagger(app))
