#!/usr/bin/env python
#coding=utf-8
import os, sys
import yajl as json
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

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

config = os.environ

def message(sc, ch, txt, thread):
    return sc.api_call(
      "chat.postMessage",
      channel=ch,
      text=txt,
      as_user=False,
      username="tapdone bot"
    )

def get_datetimes(event_date, event_start_time ,event_end_time):
    """
    Datetime conversion utility
    converts from date and start and end time

    Конвертирует даты, времени начала и время конца 
    в datetime начала и конца. Если время не задано ставит весь день.
    Если не задано ничего, то ставит от +15 до +30 минут от текущего времени.

    @@params
    ----------
    event_date : string                 
    event_start_time : string
    event_end_time : string

    @@returns
    ----------
    event_start_time : datetime
    event_end_time : datetimte


    """

    if event_date and event_start_time and event_end_time:
        event_start_time = "%sT%s" % (event_date, event_start_time)
        event_end_time = "%sT%s" % (event_date, event_end_time)
        event_start_time = parse(event_start_time)
        event_end_time = parse(event_end_time)
    elif event_date:
        event_start_time = "%sT%s" % (event_date, "00:00")
        event_end_time = "%sT%s" % (event_date, "23:59")
        event_start_time = parse(event_start_time)
        event_end_time = parse(event_end_time)
    else:
        event_start_time = datetime.datetime.now() + datetime.timedelta(minutes=15)
        event_end_time = event_start_time + datetime.timedelta(minutes=30)

    return event_start_time, event_end_time

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

    ai = apiai.ApiAI(config['APIAI_CLIENT_ACCESS_TOKEN'])
    users = {}

    while True:
        buf = sc.rtm_read()
        if buf == []: continue
        for item in buf:   
            if item.get('type', '') != 'message': continue
            subtype = item.get('subtype', '')
            team = item.get('team', '') or item.get('source_team', '')
            if subtype == 'bot_message' or not team: continue
            slid = item.get('user', 1)
                       
            resp =  {
                'sc' : sc, 
                'ch' : item['channel'],
                'txt' : '', 
                'thread': item['ts']
            } 

            auth = get_user_google_auth(slid)   

            if not auth:
                resp['txt'] = """\
                Looks like you are not authorized. To authorize Google Calendar open this url in browser %s?slid=%s&tid=%s\
                """ % (config['GOOGLE_API_REDIRECT_URL'], slid, team)
                message(**resp)
                continue      

            elif auth == 'multiple':
                resp['txt'] = """\
                Looks like you have multiple records for your id. Contact the app admin.\
                """
                message(**resp)
                continue    
            
            msg = item.get('text', '')
            msg_type, event_text, event_start_time, event_end_time, event_date, speech = get_ai_response(ai, slid, msg)

            if not speech: continue

            resp['txt'] = speech

            if msg_type == 'Create task':
                event_start_time, event_end_time = get_datetimes(event_date, event_start_time, event_end_time)
                e, e_resp = create_event(auth, event_text, event_start_time, event_end_time)            
                resp['txt'] += "\nEvent link: {link} .\n".format(link=e['htmlLink']) + e_resp

            message(**resp)

def get_tokens():
    """
    Gets tokens via api    

    """
    h = httplib2.Http(".cache")
    (resp_headers, content) = h.request(config['FLASK_PROTOCOL']+"://"+config['FLASK_HOST']+"/api/v1/get_tokens", "GET")
    tokens = [ x for x in  json.loads(content)['tokens'] if x is not None ]
    return set(tokens)

def get_user_google_auth(slid):
    """
    Gets user's calendar authentication
    
    @@params
    ----------
    slid : string
           slack team id

    """
    h = httplib2.Http(".cache")
    format_string = config['FLASK_PROTOCOL']+"://"+config['FLASK_HOST']+"/api/v1/get_user_google_auth?slid=%s"
    url = format_string % slid 
    (resp_headers, content) = h.request(url, "GET")
    
    if not content:
        return False
    
    jsn = json.loads(content)    
    val = jsn.get('google_auth', False)

    return val


class Handler:
    """
    Handls thread spawn requests.
    Keeps track on not unique tokens.

    Асинхронный хендлер, который создает потоки slack_messaging, к
    огда приходит http запрос на урл
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
        if token not in self.running:
            try:
                t = threading.Thread(target=slack_messaging, args=(token,))
                t.daemon = True
                t.start()
            except:
                return web.Response(text=str(sys.exc_info()[0]))

        return web.Response(text='ok')

def main():
    # getting tokens via api
    tokens = get_tokens()

    # spawning initial threads
    # потоки по slack_messaging полученным из токе
    if len(tokens)  > 0 :
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(len(tokens))
        for token in tokens:
            q = asyncio.ensure_future(loop.run_in_executor(executor, slack_messaging, token))

    # starting thread spawning application
    # тут запускается веб-приложение на aiohttp, которое обрабатывает запросы
    # на открытие slack_messaging
    app = web.Application()
    handler = Handler(tokens)
    app.router.add_get('/slack_api/v1/slack_team_process', handler.handle_slack_team)
    web.run_app(app, host=config['SLACK_HOST'], port=int(config['SLACK_PORT']))

    loop.run_forever()

if __name__ == "__main__":
    main()

