#!/usr/bin/env python
#coding=utf-8
import os, sys
import json
import datetime
import shortuuid
import asyncio
from utils.calendar import create_event
from dateutil.parser import *
import pytz
import httplib2

from slackclient import SlackClient
from aiohttp import web

from utils.lib import get_or_create
from utils.http_libs import get_user_google_auth, get_tokens, get_ai_response, get_token, create_calendar_event

import logging
import logging.config
import argparse

from config import logging_config

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument('--path')
parser.add_argument('--port')

logger = logging.getLogger()
logging.config.dictConfig(logging_config)
config = os.environ

authed_teams = {}

class Handler:  
    def __init__(self, verification):
        self.verification = verification

    async def check_auth(self, slid):
        auth = await get_user_google_auth(slid) # get user google calendar auth
        message = False

        if not auth:
            message = """\
            Looks like you are not authorized. To authorize Google Calendar open this url in browser {}?slid={}&tid={}\
            """.format(config['GOOGLE_API_REDIRECT_URL'], slid, team)
        elif auth == 'multiple':
            message = """\
            Looks like you have multiple records for your id. Contact the app admin.\
            """
        return auth, message

    def message(sc, ch, txt, thread):
        return sc.api_call(
          "chat.postMessage",
          channel=ch,
          text=txt,
          as_user=False,
          username="tapdone bot"
        )


    async def process_message(self, slack_event):
        team = slack_event.get('team_id', '')
        ev = slack_event['event']
        ev_type = ev['type']        
        slid = ev.get('user', '')
        msg = ev.get('text', '')
        ts = ev.get('ts', '')
        channel = ev.get('channel', '')
        bot_token = authed_teams.get(team, '')



        if not bot_token:
            bot_token = await get_token(team)
            if bot_token:
                authed_teams[team] = bot_token
            else:
                return

        sc = SlackClient(bot_token)

        resp =  {
            'sc' : sc, 
            'ch' : channel,
            'txt' : '',
            'thread': ts
        }

        auth, auth_message = await self.check_auth(slid)

        if auth_message:
            resp['txt'] = auth_message
            self.message(**resp)
            return
 
        # if not or(ev_type, team, slid, msg):
        #     return 

        ai_response = await get_ai_response(slid, msg)

        msg_type = ai_response['msg_type']
        event_text = ai_response['event_text']
        event_start_time = ai_response['event_start_time']
        event_end_time = ai_response['event_end_time']
        event_date = ai_response['event_date']
        speech = ai_response['speech']

        if not speech: return

        if msg_type == 'Create task':
            user_response = await create_calendar_event(
                msg_type,
                event_text,
                event_start_time,
                event_end_time,
                event_date,
                speech,
            )

        self.message(**resp)
           

    async def handle_incoming_event(self, request):
        # read request body and parse json
        body = await request.text()

        if not body or not isinstance(body, str):
            return web.Response(text='could not parse json')

        slack_event = json.loads(body)
        logger.info(slack_event)

        # ============= Slack URL Verification ============ #
        # In order to verify the url of our endpoint, Slack will send a challenge
        # token in a request and check for this token in the response our endpoint
        # sends back.
        #       For more info: https://api.slack.com/events/url_verification    
        if "challenge" in slack_event:
            return web.json_response(slack_event["challenge"])
            

        # ============ Slack Token Verification =========== #
        # We can verify the request is coming from Slack by checking that the
        # verification token in the request matches our app's settings
        if self.verification != slack_event.get("token"):
            message = "Invalid Slack verification token"
            # By adding "X-Slack-No-Retry" : 1 to our response headers, we turn off
            # Slack's automatic retries during development.
            return web.json_response(message, status=403)        


        if not 'event' in slack_event:
            return web.Response(text='no event found, skipping')

        ev = slack_event['event']
        ev_type = ev['type']

        if ev_type == 'message':
            await self.process_message(slack_event)

        return web.Response(text='ok')

    async def handle_new_team(self, request):
        # read request body and parse json
        team_data = await request.json()
        team_id = team_data.get('team_id', '')
        bot_token = team_data.get('bot_token', '')
        
        if team_id and bot_token:
            authed_teams[team_id] = bot_token

    async def get_ai_response(self, slid, msg):
        """
        Gets api ai response text based on message
        extracts events time, date and response to user.
        """
        data = await request.json()

        slid = in_jsn['slid']
        msg = in_jsn['msg']

        ai = apiai.ApiAI(config['APIAI_CLIENT_ACCESS_TOKEN'])
        request = ai.text_request()
        request.session_id = slid
        request.query = msg
        airesponse = json.loads(request.getresponse().read().decode('utf8'))

        res = airesponse.get('result',{})
        msg_type = res.get('metadata', {}).get('intentName','')
        params = res.get('parameters', {})
        event_text = params.get('any', "Test task text")
        event_time = params.get('time', [])

        if isinstance(event_time, list):
            if len(event_time) == 2:            
                event_start_time = event_time[0]
                event_end_time = event_time[1]

            elif len(event_time) == 1:
                event_start_time = event_time[0]
                event_end_time = False
                
            else:
                event_start_time = False
                event_end_time = False
        else:
            event_start_time = event_time
            event_end_time = False

        event_date = params.get('date', '')
        speech = res.get('fulfillment', {}).get('speech', '')

        resp = {
            'msg_type': msg_type, 
            'event_text': event_text, 
            'event_start_time': event_start_time, 
            'event_end_time': event_end_time, 
            'event_date': event_date, 
            'speech':  speech,
        }

        return jsonify(resp), 200




async def init_tokens(app):
    tokens = await get_tokens()
    logging.info(tokens)
    for key, value in tokens:
        authed_teams[key] = value

    
def init_app():
    app = web.Application()
    app.on_startup.append(init_tokens)
    handler = Handler(config['SLACK_VERIFICATION_TOKEN'])
    app.router.add_post('/slack_api/v1/incoming_event_handler', handler.handle_incoming_event)
    app.router.add_get('/slack_api/v1/new_slack_team', handler.handle_new_team)
    app.router.add_get('/slack_api/v1/get_ai_response', handler.handle_new_team)
    return app


def main():
    args = parser.parse_args()
    app = init_app()
    # web.run_app(app, host=args.path)
    web.run_app(app, host=config['SLACK_HOST'], port=int(config['SLACK_PORT']))


if __name__ == "__main__":    
    try:
       main()
    except Exception as e:
        logger.exception(e)
        raise
    
