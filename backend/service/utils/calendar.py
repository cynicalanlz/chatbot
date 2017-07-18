#!/usr/bin/env python
#coding=utf-8
import os
import httplib2
import datetime
import yajl as json
from flask import render_template, make_response

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow, Credentials

from dateparser import parse
import pytz

config = os.environ

import logging, sys

def get_service(creds):
    """
    Authorizes google calendar
    """
    logging.info('service1')
    http = httplib2.Http()
    logging.info('service2')
    http = creds.authorize(http)
    logging.info('service3')
    service = discovery.build('calendar', 'v3', http=http)
    logging.info('service4')
    return service


def get_events(service):
    """
    Gets all upcoming events from google calendar for checking overlaps
    """
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=2500, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    rsp = []

    if not events or not len(events) > 0:
        return rsp
    
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
    """
    Gets user primary calendar id for detecting settings
    """
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

def create_event(google_auth, event_text, event_start_new, event_end_new):
    """
    Checks for overlaps and creates the event in google calendar

    Получает текст события, datetime начала и конца события без таймзоны.

    Авторизуется по авторизационным данным в гугл календаре, делает http запрос 
    и получает до 2500 предостоящих событий. 

    Получает таймзону из календаря, делает timezone-aware datetime из дат начала и конца события.
    Если есть пересечения, то пишет в ответ что они есть.
    
    Возвращает полученный объект события и текст, если есть пересечения.

    """
    logging.info('in google auth')
    auth = json.loads(google_auth)
    logging.info('cal1')    
    logging.info(auth)
    if not auth:
        logging.info('auth is false')
    creds = Credentials.new_from_json(auth)
    logging.info('cal2')    
    if creds and not creds.invalid:
        logging.info('cal2.1')    
        service = get_service(creds)
        logging.info('cal2.2')    
    else:
        logging.info("incorrect credentials")

    logging.info('cal3')    
    events = get_events(service)        
    logging.info('cal4')    
    primary_calendar = get_primary_calendar(service)
    logging.info('cal5')    
    tz = service.settings().get(setting='timezone').execute()
    if tz:
        tz = tz['value']
    else:
        tz = 'America/Los_Angeles'
    logging.info('cal6')    
    

    timezone = pytz.timezone(tz)
    event_start_new = timezone.localize(event_start_new)
    event_end_new = timezone.localize(event_end_new)

    parse_settings = {'RETURN_AS_TIMEZONE_AWARE': True}
    overlap_texts_format_string = '- {}, which is between {} - {};\n'
    logging.info('cal7') 

    res = ''   

    if events and len(events) > 0:     
        logging.info('cal8')    
        overlap_texts = []
        logging.info('cal9')    

        for start, end, summary in events:  
            logging.info('cal9.1')        
            if start and end:
                logging.info('cal9.2')        
                event_start = parse(start, settings=parse_settings)
                logging.info('cal10')    
                event_end = parse(start, settings=parse_settings)
                logging.info('cal11')    
                if event_start == event_start_new and event_end == event_end_new:
                    logging.info('cal12')    
                    overlap_text = overlap_texts_format_string.format(summary, event_start, event_end)
                    overlap_texts.append(overlap_text)
                    logging.info('cal13')    

                logging.info('cal14')   
                if has_overlap(event_start, event_end, event_start_new, event_end_new):
                    logging.info('cal15')   
                    overlap_text = overlap_texts_format_string.format(summary, event_start, event_end)
                    overlap_texts.append(overlap_text)
                    logging.info('cal16')   

        logging.info(overlap_texts)

        if len(overlap_texts) > 0:
            logging.info('len > 0')
            ovarlaps_joined = ''.join(overlap_texts)                
            res +=  'Overlaps with: \n {texts}.'.format(texts=ovarlaps_joined)

    logging.info('cal18')   

    event = {
      'summary': event_text,
      # 'location': '800 Howard St., San Francisco, CA 94103',
      # 'description': 'A chance to hear more about Google\'s developer products.',
      'start': {
        'dateTime':  event_start_new.isoformat("T"),
        # 'timeZone': tz,
      },
      'end': {
        'dateTime': event_end_new.isoformat("T"),
        # 'timeZone': tz,
      },
      'reminders': {
        'useDefault': False,
        'overrides': [
          {'method': 'email', 'minutes': int(config['DEFAULT_NOTIFY_MINUTES']) },
          {'method': 'popup', 'minutes': int(config['DEFAULT_NOTIFY_MINUTES']) },
        ],
      },
    }
    logging.info('cal20')    

    event = service.events().insert(calendarId=primary_calendar, body=event).execute()
    
    logging.info('cal21')    

    return event, res
    