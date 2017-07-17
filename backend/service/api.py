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



api = Blueprint('api', __name__)


v = '/v1/'

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

def slack_team_process(token):
    """
    Makes api call to spawn slack team thread to slack

    Делает запрос по api, чтобы создать процесс по обработке
    потока событий слек команды

    @@params
    ----------
    event_date : string      
    """
    h = httplib2.Http(".cache")    
    format_string = config['SLACK_PROTOCOL']+"://"+config['SLACK_HOST']+"/slack_api/v1/slack_team_process?token=%s"    
    url = format_string % token
    (resp_headers, content) = h.request(url, "GET")
    return resp_headers

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

    if not auth_response.get('ok',False):
        return jsonify({'msg' : 'not ok'})
    
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

    code = request.args('code')
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

    tokens = [x[0] for x in db.session.query(SlackTeam.bot_token).distinct()]

    response = {
        'tokens' : tokens
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
            'google_auth' : False
        }), 404
    except MultipleResultsFound:
        return jsonify({
            'google_auth' : 'multiple'
        }), 404

    auth = usr.google_auth

    if not auth:
        return jsonify({
            'google_auth' : False
        }), 404

    jsn = json.loads(auth)
    credentials = Credentials.new_from_json(jsn)

    if credentials.invalid or not credentials:                
        return jsonify({
            'google_auth' : False,
            'reason' : 'invalid'
        }), 404                

    if credentials.access_token_expired:
        h = httplib2.Http(".cache")
        credentials.refresh(h)            
        usr.google_auth = json.dumps(credentials.to_json())
        db.session.commit()
                 
        return jsonify({
            'google_auth' : credentials.to_json()                    
        }), 200

            
    return jsonify({
        'google_auth' : auth
    }), 200


@api.route('/health')
def health():
    response = {
        'health': 'ENABLED'
    }

    return jsonify(response), 200