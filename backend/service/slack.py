#!/usr/bin/env python

import os
import yajl as json
import datetime
import shortuuid
from slackclient import SlackClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import asyncio

from utils.calendar import create_event
from user.models import User, SlackTeam
from utils.lib import get_or_create
from concurrent.futures import ThreadPoolExecutor


from dateutil.parser import *
import pytz

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
            u, created = get_or_create(
                session, 
                User, 
                default_values={'id': shortuuid.ShortUUID().random(length=22)}, 
                slid=slid
            )

            auth = u.google_auth is not None
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
            event_text = res.get('parameters', {}).get('any', "Test task text")
            resp['txt'] = res.get('fulfillment', {}).get('speech', '')
            
            if not resp['txt']: continue
            if msg_type == 'Create task':                
                event_time = datetime.datetime.now(pytz.utc) + datetime.timedelta(minutes=15)
                e, e_resp = create_event(session, User, slid, event_text, event_time)                    
                resp['txt'] += "Event link: {link} .".format(link=e['htmlLink']) + e_resp

            pm(**resp)


if __name__ == "__main__":
    session = Session()
    tokens = [x[0] for x in session.query(SlackTeam.bot_user_id).distinct()]
    if len(tokens) > 0:

        loop = asyncio.get_event_loop()

        executor = ThreadPoolExecutor(len(tokens))


        for token in tokens:
            q = asyncio.ensure_future(loop.run_in_executor(executor, slack_messaging, token))

        loop.run_forever()