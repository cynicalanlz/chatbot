#!/usr/bin/env python
#coding=utf-8

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

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from logging.handlers import RotatingFileHandler

from utils.calendar import create_event

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai


api = Blueprint('api', __name__)
v = '/v1/'


import logging, sys

LOG_FILENAME = 'api.log'

fileHandler = RotatingFileHandler(LOG_FILENAME, maxBytes=20971520,
                                  backupCount=5, encoding='utf-8')
fileHandler.setLevel(logging.DEBUG)
filefmt = '%(asctime)s [%(filename)s:%(lineno)d] %(message)s'
fileFormatter = logging.Formatter(filefmt)
fileHandler.setFormatter(fileFormatter)

logger = logging.getLogger(__name__)
logger.addHandler(fileHandler)



def registered_user_page(creds, usr):
    """
    Страница зарегистрированного пользователя гугл    
    """
    return make_response(
        render_template(
            'registered.html',
        ))


@api.route(v+'register_slack_team')
def register_slack_team():
    """
    View with a button for slack registration.

    @@params
    ----------
    event_date : string                 
    event_start_time : string
    event_end_time : string

    """
    return render_template('register_slack.html')

def new_slack_team(token, team_id):
    """
    Makes api call to spawn slack team thread to slack

    Делает запрос по api, чтобы создать процесс по обработке
    потока событий слек команды

    @@params
    ----------
    event_date : string      
    """
    h = httplib2.Http(".cache")    
    format_string = config['SLACK_PROTOCOL']+"://"+config['SLACK_HOST'] + ":" + config['SLACK_PORT'] +"/slack_api/v1/new_slack_team?token={}&team_id={}"        
    url = format_string.format(token,team_id)
    logging.info(url)
    (resp_headers, content) = h.request(url, "GET")
    content = content.decode('utf-8')

    if content is None or not content:
        return resp_headers, ''

    return resp_headers, content


@api.route(v+"register_slack", methods=["GET", "POST"])
def slack_post_install():
    """
    Gets a SlackTeam by id, obtained from slack auth api call
    based on token from request params

    Получает авторизационный код, который передает слек после авторизации команды 
    на его сайте.
    С помощью этого кода и ключей, которые закреплены за приложением в настройках api.slack.com
    и хранятся в конфиге, получает json объект авторизационных данных, из которого
    достает айди слек команды и авторзационные данные и пишет в объект с айди слек команды в бд.

    @@params
    ----------
    auth_code : string

    @@db exports
    ----------
    SlackTeam : obj, team tokens for bot access with id and name

    @@returns
    msg: : json string, ok / not ok

    """
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
    
    slack_tid = auth_response.get('team_id', '')

    team, created = get_or_create(
        db.session, 
        SlackTeam,
        {
            'id' : shortuuid.ShortUUID().random(length=22) 
        },
        team_id=slack_tid
    )

    logging.info(auth_response)

    if not auth_response.get('ok',False):
        return jsonify({'msg' : 'not ok'})
    
    team.team_name = auth_response['team_name']
    team.team_id = auth_response['team_id']
    team.access_token = auth_response['access_token']
    team.bot_token = auth_response['bot']['bot_access_token']
    team.bot_user_id = auth_response['bot']['bot_user_id']

    db.session.commit()

    try:
        head, cont = new_slack_team(team.team_id, team.bot_token)
        logging.info(head)

        return jsonify({
               'msg' : 'got response',
               'head' : head,
               'content' : cont
            }), int(head['status'])

    except Exception as e:
        return jsonify({
               'msg' : 'got error on new team creation'
            }), 500


@api.route(v+'register_cb')
def register_google():
    """
    If user authorization not found via user slack id  in db
    then redirects user to google, then the OAuth2 flow is completed 
    to obtain the new credentials.

    Работает в 2-х комбинациях параметров:
    
    tid, slid - получает из слека айди пользователя и айди команды,
    если по этому айди не находится объект пользователя, то создает,
    ставит куку и редиректит дальше, по сформированному url авторизации в гугле, 
    в который передает параметр state=slid, который ему потом возвращается от гугла
    code, slid - когда возвращается от гугла


    @@params
    ----------
    code : string, authorization code returned by google
    tid : string, team id passed by slack bot via url 
    slid : string, user id passed by slack bot via url 
    uid : string, our user id stored in token by team name

    @@db exports
    ----------
    User : obj, google user object

    @@returns
    msg: : json string, ok / not ok

    """

    code = request.args.get('code')
    tid = request.args.get('tid')
    slid = request.args.get('slid') or request.args.get('state')
    uid = request.cookies.get(tid) or str(shortuuid.ShortUUID().random(length=22))

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

    if usr.google_auth:
        creds = Credentials.new_from_json(json.loads(usr.google_auth))
        if creds and not creds.invalid:
            resp = registered_user_page(creds, usr)
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

    resp = registered_user_page(creds, usr)

    return resp

@api.route(v+'get_tokens')
def get_tokens():
    """
    Returns slack bot tokens for all teams from db.    

    @@returns
    tokens: : array in json

    """

    teams = db.session.query(SlackTeam).distinct()

    tokens = [(x.team_id, x.bot_token) for x in teams]

    response = {
        'tokens' : tokens
    }
    
    return jsonify(response), 200


@api.route(v+'get_token')
def get_token():
    """
    Returns slack bot token for a team

    @@returns
    token: : string

    """
    team = request.args.get('team')

    try:
        token = db.session.query(User).filter_by(slid=team).one()
    except NoResultFound:
        return jsonify({
            'error' : True,
            'token' : 'missing'
        }), 404
    except MultipleResultsFound:
        return jsonify({
            'error' : True,
            'token' : 'multiple'
        }), 404

    response = {
        'error': False,
        'token' : token
    }
    
    return jsonify(response), 200

@api.route(v+'get_user_google_auth')
def get_user_google_auth():   
    """
    Returns google authentication codde, refreshes it 
    if needed.

    Получает слек айди пользователья slid, делает выборку из бд по slid
    если нет ответа возвращает ошибку, из бд получает авторизационные данные,
    проверяет актуальность авторизационных данных, если нужно, то обновляет их
    и пишет в бд.
    Полученные проверенные данные отправляет обратно в json.

    @@params
    ----------
    slid : string, slack id

    @@db exports
    ----------
    User.google_auht : string, google credentials obtained by oath

    @@returns
    google auth: : json in json

    """
    slid = request.args.get('slid')

    try:
        usr = db.session.query(User).filter_by(slid=slid).one()
    except NoResultFound:
        return jsonify({
            'error' : True,
            'google_auth' : False
        }), 404
    except MultipleResultsFound:
        return jsonify({
            'google_auth' : 'multiple'
        }), 404

    auth = usr.google_auth

    if not auth:
        return jsonify({
            'error' : True,
            'google_auth' : False
        }), 404

    jsn = json.loads(auth)
    credentials = Credentials.new_from_json(jsn)

    if credentials.invalid or not credentials:                
        return jsonify({
            'error' : True,
            'google_auth' : False,
            'reason' : 'invalid'
        }), 404                

    if credentials.access_token_expired:
        h = httplib2.Http()
        credentials.refresh(h)            
        usr.google_auth = json.dumps(credentials.to_json())
        db.session.commit()
                 
        return jsonify({
            'error' : False,
            'google_auth' : json.dumps(credentials.to_json())
        }), 200

    return jsonify({
        'error' : False,
        'google_auth' : json.dumps(credentials.to_json())
    }), 200

#----------------------------------------------
# ----------- slack ---------------------------
#----------------------------------------------


@api.route(v+'create_calendar_event')
def create_calendar_event():
    data = request.data
    jsn = json.loads(data)
    google_auth = jsn['google_auth']
    event_text = jsn['event_text']
    event_date = jsn['event_date']
    event_start_time = jsn['event_start_time']
    event_end_time = jsn['event_end_time']
    response = create_event(google_auth, event_text, event_date, event_start_time, event_end_time)
    json_resp = {
        'response' : response
    }
    return jsonify(json_resp), 200

#-----------------------------------
# ----------- misc -----------------
#-----------------------------------


@api.route('/health')
def health():
    response = {
        'health': 'ENABLED'
    }

    return jsonify(response), 200
