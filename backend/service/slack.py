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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from user.models import User, SlackTeam
from utils.lib import get_or_create

try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

config = os.environ

# an Engine, which the Session will use for connection
# resources
pg_engine = create_engine(config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(bind=pg_engine)

def pm(sc, ch, txt, thread):
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
    session = Session()

    while True:
        buf = sc.rtm_read()
        if buf == []: continue                
        for item in buf:            
            if item['type'] != 'message': continue

            msg = item.get('text', '')
            subtype = item.get('subtype', '')
            team = item.get('team', '') or item.get('source_team', '')
            if subtype == 'bot_message' or not team: continue

            slid = item.get('user', 1)
            auth = session.query(User.google_auth).filter_by(slid=slid).first()
            resp =  {
                'sc' : sc, 
                'ch' : item['channel'],
                'txt' : '', 
                'thread': item['ts']
            } 

            if not auth:
                resp['txt'] = """\
                Looks like you are not authorized. To authorize Google Calendar open this url in browser %s?slid=%s&tid=%s\
                """ % (config['GOOGLE_API_REDIRECT_URL'], slid, team)
                pm(**resp)
                continue
        
            request = ai.text_request()
            request.session_id = slid
            request.query = msg
            airesponse = json.loads(request.getresponse().read().decode('utf8'))

            res = airesponse.get('result',{})
            msg_type = res.get('metadata', {}).get('intentName','')
            params = res.get('parameters', {})
            event_text = params.get('any', "Test task text")
            event_time = params.get('time', [])
            event_date = params.get('date', '')
            
            if len(event_time) == 2:            
                event_start_time = event_time[0]
                event_end_time = event_time[1]

            resp['txt'] = res.get('fulfillment', {}).get('speech', '')
            
            if not resp['txt']: continue
            if msg_type == 'Create task':

                if event_date and event_time and event_end_time:
                    event_start_time = "%sT%s" % (event_date, event_start_time)
                    event_end_time = "%sT%s" % (event_date, event_end_time)
                    event_start_time = parse(event_start_time).replace(tzinfo=pytz.timezone('America/Los_Angeles'))
                    event_end_time = parse(event_end_time).replace(tzinfo=pytz.timezone('America/Los_Angeles'))

                else:
                    event_start_time = datetime.datetime.now(pytz.timezone('America/Los_Angeles')) + datetime.timedelta(minutes=15)
                    event_end_time = event_start_time + datetime.timedelta(minutes=30)

                e, e_resp = create_event(
                    session, User, slid, event_text, 
                    event_start_time, event_end_time) 
                
                resp['txt'] += "Event link: {link} .".format(link=e['htmlLink']) + e_resp

            pm(**resp)

def get_tokens():
    h = httplib2.Http(".cache")
    (resp_headers, content) = h.request("http://127.0.0.1/api/v1/get_tokens", "GET")
    tokens = [ x for x in  json.loads(content)['tokens'] if x is not None]
    return set(tokens)


async def handle(request):
    token = request.query.get('token', "") 
    t = threading.Thread(target=slack_messaging, args=(token,))
    t.daemon = True
    t.start()
    return web.Response(text='ok')

def main():
    tokens = get_tokens()
        
    if len(tokens)  > 0 :
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(len(tokens))
        for token in tokens:
            q = asyncio.ensure_future(loop.run_in_executor(executor, slack_messaging, token))

    app = web.Application()
    app.router.add_get('/slack_team_process', handle)
    web.run_app(app, host='127.0.0.1', port=8080)

    loop.run_forever()

if __name__ == "__main__":
    main()

