import json
import datetime, pytz

def get_ai_response(ai, slid, msg):

    request = ai.text_request()
    request.session_id = slid
    request.query = msg
    airesponse = json.loads(request.getresponse().read().decode('utf8'))

    res = airesponse.get('result',{})
    msg_type = res.get('metadata', {}).get('intentName','')
    params = res.get('parameters', {})
    event_text = params.get('any', "Test task text")
    event_time = params.get('time', [])

    if len(event_time) == 2:            
        event_start_time = event_time[0]
        event_end_time = event_time[1]
    else:
        event_start_time = False
        event_end_time = False

    event_date = params.get('date', '')
    speech = res.get('fulfillment', {}).get('speech', '')

    return msg_type, event_text, event_start_time, event_end_time, event_date, speech