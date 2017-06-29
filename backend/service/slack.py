#!/usr/bin/env python

import os
import yajl as json
from slackclient import SlackClient

from user.models import User

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.lib import get_or_create
import shortuuid

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

def slack_messaging():
    sc = SlackClient(config['SLACK_LEGACY_TOKEN'])

    if not sc.rtm_connect():
        print("App is using legacy token, which probably should be used from one pc only. Connection Failed, invalid token?")
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
            if subtype == 'bot_message' or not msg: continue

            usr = item.get('user', 1)
            u, created = get_or_create(session, User, default_values={'id': shortuuid.ShortUUID().random(length=22)}, slid=usr)

            print (u, u.id, u.slid)
            auth = u.google_auth is not None     

            print (u.google_auth, not auth, not created, not created and not auth)

            if auth:
                request = ai.text_request()
                request.session_id = usr
                request.query = msg
                response = json.loads(request.getresponse().read().decode('utf8'))
                print (response)
                response_text = response.get('result', {}).get('fulfillment', {}).get('speech', '')
            else:
                response_text = "Looks like you are not authorized. To authorize Google Calendar open this url in browser %s?slid=%s" % (config['GOOGLE_API_REDIRECT_URL'], usr)
            
            if not response_text: continue
                
            m = sc.api_call(
              "chat.postMessage",
              channel=item['channel'],
              text=response_text,
              thread_ts=item['ts']
            )


if __name__=='__main__':
	slack_messaging()