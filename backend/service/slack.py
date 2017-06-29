#!/usr/bin/env python

import os
import yajl as json

from slackclient import SlackClient
try:
    import apiai
except ImportError:
    sys.path.append(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
    )
    import apiai

config = os.environ

def slack_messaging():
    sc = SlackClient(config['SLACK_LEGACY_TOKEN'])

    if not sc.rtm_connect():
        print("Connection Failed, invalid token?")
        return

    while True:
        buf = sc.rtm_read()
        if buf == []: continue                
        for item in buf:            
            if item['type'] != 'message': continue

            msg = item.get('text', '')
            subtype = item.get('subtype', '')
            if subtype == 'botmessage': continue

            ai = apiai.ApiAI(config['APIAI_CLIENT_ACCESS_TOKEN'])
            request = ai.text_request()
            request.session_id = '1' #"<SESSION ID, UNIQUE FOR EACH USER>"
            request.query = msg
            response = json.loads(request.getresponse().read().decode('utf8'))
            response_text = response.get('result', {}).get('fulfillment', {}).get('speech', '')
            if not response_text: continue
                
            m = sc.api_call(
              "chat.postMessage",
              channel=item['channel'],
              text=response_text,
              thread_ts=item['ts']
            )


if __name__=='__main__':
	slack_messaging()