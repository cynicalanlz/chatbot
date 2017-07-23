#!/usr/bin/env python
#coding=utf-8
import os, sys
import json
import datetime
import shortuuid
import asyncio
from utils.calendar import create_event
from concurrent.futures import ThreadPoolExecutor
from dateutil.parser import *
import pytz
import httplib2

from slackclient import SlackClient
import threading
from aiohttp import web

from utils.lib import get_or_create
from utils.ai import get_ai_response
from utils.http_libs import get_user_google_auth, get_tokens

import logging
import logging.config
import argparse

parser = argparse.ArgumentParser(description="aiohttp server example")
parser.add_argument('--path')
parser.add_argument('--port')

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": '%(asctime)s [%(filename)s:%(lineno)d] : %(message)s'
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "slack_app.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": "slack_app_error.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    },

    "loggers": {
        "aiohttp.access": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.client": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.internal": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.access": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.server": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.web": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aaiohttp.websocket": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        }

    },

    "root": {
        "level": "INFO",
        "handlers": ["console", "info_file_handler", "error_file_handler"]
    }
}

logger = logging.getLogger(__name__)
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


def check_auth(slid):
    auth = get_user_google_auth(slid) # get user google calendar auth
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

def slack_messaging(token):
    """
    Main slack messaging process. 

    Could be parralel if tokens unique


    Процесс, который соединяется по вебсокету со серверами слека,
    получает поток массивов, внутри которых json объекты соообщений
    и события команды слека.

    Если получает json формата "сообщение" и пользователь авторизован, 
    то отправляет данные в api.ai, получает ответ и отправляет пользователю.
    Если необходимо создает задачу.


    @@params
    ----------
    token : string
            token for slack team

    """
    sc = SlackClient(token)    
    if not sc.rtm_connect():
        print("""\
        App is using legacy token, which probably should be used from one pc only. Connection Failed, invalid token\
        """)
        return

    users = {}

    while True:
        buf = sc.rtm_read() # reads all events
        if buf == []: continue # if no events skips
        for item in buf:
            if item.get('type', '') != 'message': continue # skip not message events      
            team = item.get('team', '') or item.get('source_team', '')
            subtype = item.get('subtype', '')
            if subtype == 'bot_message' or not team: continue # skip bot messsages
            slid = item.get('user', 1)            
                       
            resp =  {
                'sc' : sc, 
                'ch' : item['channel'],
                'txt' : '',
                'thread': item['ts']
            }

            auth, auth_message = check_auth(slid)

            if auth_message:
                resp['txt'] = auth_message
                message(**resp)
                continue
            
            msg = item.get('text', '')
            msg_type, event_text, event_start_time, \
                event_end_time, event_date, speech = get_ai_response(slid, msg) # get response from api.ai

            if not speech: continue

            resp['txt'] = speech

            if msg_type == 'Create task':
                
                e, e_resp = create_event(
                    auth, 
                    event_text,
                    event_date,
                    event_start_time, 
                    event_end_time
                )            
                resp['txt'] += "\nEvent link: {link} .\n".format(link=e['htmlLink']) + e_resp
                
            message(**resp)

class Handler:
    """
    Handls thread spawn requests.
    Keeps track on not unique tokens.
    Асинхронный хендлер, который создает потоки slack_messaging, 
    когда приходит http запрос на урл
    /slack_api/v1/slack_team_process
    """
    def __init__(self, tokens):
        self.running = tokens

    @asyncio.coroutine
    def handle_slack_team(self, request):
        """
        Async handler couroutine that spawns threads
        """
        token = request.query.get('token', "")
        self.running.add(token)
        # if token not in self.running:
        try:
            if token:
                t = threading.Thread(target=slack_messaging, args=(token,))
                t.daemon = True
                t.start()
            else:
                return web.Response(text='no token found')
        except:
            return web.Response(text=str(sys.exc_info()[0]))

        return web.Response(text='ok')

def init_app(tokens):
    app = web.Application()
    handler = Handler(tokens)
    app.router.add_get('/slack_api/v1/slack_team_process', handler.handle_slack_team)
    return app

def main():
    tokens = get_tokens()

    # logging.info(tokens)

    # spawning initial threads
    if len(tokens)  > 0 :
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(len(tokens))
        for token in tokens:
            q = asyncio.ensure_future(loop.run_in_executor(executor, slack_messaging, token))


    args = parser.parse_args()
    app = init_app(tokens)
    # web.run_app(app, host=args.path)
    web.run_app(app, host=config['SLACK_HOST'], port=int(config['SLACK_PORT']))

if __name__ == "__main__":    
    try:
        main()
    except Exception as e:
        logging.exception(e)
        raise
    