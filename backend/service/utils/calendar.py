import httplib2
import datetime
import yajl as json
from flask import render_template, make_response

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow, Credentials

from dateutil.parser import *

def get_service(creds):
    http = httplib2.Http()
    http = creds.authorize(http)
    service = discovery.build('calendar', 'v3', http=http)
    return service

def get_events(service):
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        rsp = 'No upcoming events found.'        
    else:
        rsp = []

        for event in events:
            if 'start' in event:
                start = event['start'].get('dateTime', event['start'].get('date')) or ''
            if 'end' in event:                
                end = event['end'].get('dateTime', event['end'].get('date')) or ''
            if 'summary' in event:
                summary = event['summary'] or ''

            rsp.append((start, end, summary))

    return rsp

def get_primary_calendar(service):
    calendar_list = service.calendarList().list().execute()
    
    primary_id = False

    for cal in calendar_list['items']:
        if cal.get('primary', False):
         primary_id = cal['id']

    return primary_id

def has_overlap(A_start, A_end, B_start, B_end):
    latest_start = max(A_start, B_start)
    earliest_end = min(A_end, B_end)
    return latest_start <= earliest_end

def create_event(sess, usr, slid, event_text, event_time):
    usr = sess.query(usr).filter_by(slid=slid).first()
    creds = Credentials.new_from_json(json.loads(usr.google_auth))

    print (creds, creds.invalid)
    if not creds or creds.invalid:
        return "Can't find your slid. Are you registered?"

    service = get_service(creds)
    events = get_events(service)
    
    new_start = event_time
    new_end = event_time + datetime.timedelta(minutes=30)

    overlap_texts = []

    for start, end, summary in events:
        event_start = parse(start)
        event_end = parse(end)

        if has_overlap(event_start, event_end, new_start, new_end):
            overlap_texts.append('%s, which is between %s - %s' % (summary, event_start, event_end))

    if len(overlap_texts) > 0:
        res =  'Overlaps with: %s.' % (','.join(overlap_texts))
    else:
        res = ''

    
    primary_calendar = get_primary_calendar(service)    
    
    event = {
      'summary': event_text,
      # 'location': '800 Howard St., San Francisco, CA 94103',
      # 'description': 'A chance to hear more about Google\'s developer products.',
      'start': {
        'dateTime':  new_start.isoformat('T'),
        'timeZone': 'America/Los_Angeles',
      },
      'end': {
        'dateTime': new_end.isoformat('T'),
        'timeZone': 'America/Los_Angeles',
      }
    }

    event = service.events().insert(calendarId=primary_calendar, body=event).execute()
 

    return res
    