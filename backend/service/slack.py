#!/usr/bin/env python

import os
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
      thread_ts=thread,
      as_user=False,
      username="tapdone bot"
    )


def slack_messaging(token):
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
            
            msg = item.get('text', '')
            msg_type, event_text, event_start_time, event_end_time, event_date, speech = get_ai_response(ai, slid, msg)

            if not speech: continue

            resp['txt'] = speech

            if msg_type == 'Create task':        

                if event_date and event_start_time and event_end_time:
                    event_start_time = "%sT%s" % (event_date, event_start_time)
                    event_end_time = "%sT%s" % (event_date, event_end_time)
                    event_start_time = parse(event_start_time).replace(tzinfo=pytz.timezone('America/Los_Angeles'))
                    event_end_time = parse(event_end_time).replace(tzinfo=pytz.timezone('America/Los_Angeles'))

                else:
                    event_start_time = datetime.datetime.now(pytz.timezone('America/Los_Angeles')) + datetime.timedelta(minutes=15)
                    event_end_time = event_start_time + datetime.timedelta(minutes=30)

                e, e_resp = create_event(auth, event_text, event_start_time, event_end_time)
                
                resp['txt'] += "Event link: {link} .".format(link=e['htmlLink']) + e_resp


            message(**resp)

def get_tokens():
    h = httplib2.Http(".cache")
    (resp_headers, content) = h.request(config['FLASK_PROTOCOL']+"://"+config['FLASK_HOST']+"/api/v1/get_tokens", "GET")
    tokens = [ x for x in  json.loads(content)['tokens'] if x is not None ]
    return set(tokens)

def get_user_google_auth(slid):
    h = httplib2.Http(".cache")
    format_string = config['FLASK_PROTOCOL']+"://"+config['FLASK_HOST']+"/api/v1/get_user_google_auth?slid=%s"
    url = format_string % slid 
    print (url)
    (resp_headers, content) = h.request(url, "GET")
    jsn = json.loads(content)
    return jsn['google_auth']


async def handle(request):
    token = request.query.get('token', "") 
    t = threading.Thread(target=slack_messaging, args=(token,))
    t.daemon = True
    t.start()
    return web.Response(text='ok')

def main():
    tokens = get_tokens()

    i=0
        
    if len(tokens)  > 0 :
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(len(tokens))
        for token in tokens:
            q = asyncio.ensure_future(loop.run_in_executor(executor, slack_messaging, token))

    app = web.Application()
    app.router.add_get('/slack_team_process', handle)
    web.run_app(app, host=config['SLACK_HOST'], port=int(config['SLACK_PORT']))

    loop.run_forever()

if __name__ == "__main__":
    main()

