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
from utils.ai import get_ai_response
from utils.http_libs import get_user_google_auth, get_tokens, get_ai_response, get_token

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


def message(sc, ch, txt, thread):
    return sc.api_call(
      "chat.postMessage",
      channel=ch,
      text=txt,
      as_user=False,
      username="tapdone bot"
    )

authed_teams = {}


class Handler:  
    def __init__(self, pyBot, slack):
        self.bot = pyBot

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


    async def process_message(self, slack_event):
        ev = slack_event['event']
        ev_type = ev['type']
        team = ev.get('team', '')
        slid = ev.get('user', '')
        msg = ev.get('message', '')
        ts = ev.get('ts', '')
        channel = ev.get('channel', '')
        bot_token = authed_teams.get(team, '')

        if not bot_token:
            bot_token = get_token(team)
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

        auth, auth_message = await check_auth(slid)

        if auth_message:
            resp['txt'] = auth_message
            message(**resp)
            return
 
        if not or(ev_type, team, slid, msg):
            return 

        ai_response = await get_ai_response()

        msg_type = airesponse['msg_type']
        event_text = airesponse['event_text']
        event_start_time = airesponse['event_start_time']
        event_end_time = airesponse['event_end_time']
        event_date = airesponse['event_date']
        speech = airesponse['speech']

        if not speech: return
        
        auth, auth_message = check_auth(slid)


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
        if self.bot.verification != slack_event.get("token"):
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
        body = await request.text()

    
def init_app():
    handler = Handler(pyBot, slack)
    app = web.Application()
    pyBot = Bot()
    slack = pyBot.client

    app.router.add_post('/slack_api/v1/incoming_event_handler', handler.handle_incoming_event)
    return app


def main():
    tokens = get_tokens()
    for key, value in tokens:
        authed_teams[key] = value

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
    
