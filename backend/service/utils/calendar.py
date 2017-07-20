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
    http = httplib2.Http()
    http = creds.authorize(http)
    service = discovery.build('calendar', 'v3', http=http)
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


def datetime_to_rfc(dt):
    """Return a RFC3339 date-time string corresponding to the given
    datetime object."""
    if dt.utcoffset() is not None:
        return dt.isoformat()
    else:
        return "%sZ" % dt.isoformat()

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
    auth = json.loads(google_auth)
    

    creds = Credentials.new_from_json(auth)
    service = get_service(creds)

    if not auth or not creds or creds.invalid:
        return [], ''
    
    service = get_service(creds)
    events = get_events(service)
    primary_calendar = get_primary_calendar(service)
    tz = service.settings().get(setting='timezone').execute()
    default_length = service.settings().get(setting='defaultEventLength').execute()

    if default_length:
        default_length = int(default_length['value'])
        
    if tz:
        tz = tz['value']
    else:
        tz = 'America/Los_Angeles'
    
    logging.info(tz)    
    timezone = pytz.timezone(tz) # @@TODO check if timezones match or actually exist

    logging.info(not event_start_new or not event_end_new)

    if not event_start_new or not event_end_new:
        event_start_new = datetime.datetime.now() + datetime.timedelta(minutes=15)
        event_end_new = event_start_new + datetime.timedelta(minutes=default_length)

    logging.info(event_start_new)
    logging.info(event_end_new)

    event_start_new = timezone.localize(event_start_new)
    event_end_new = timezone.localize(event_end_new)

    parse_settings = {'RETURN_AS_TIMEZONE_AWARE': True}

    overlap_texts_format_string = '- {}, which is between {} - {};\n'

    res = ''   

    if events and len(events) > 0:     
        overlap_texts = []
        for start, end, summary in events:  
            if start and end:
                event_start = parse(start, settings=parse_settings)
                event_end = parse(start, settings=parse_settings)
                if event_start == event_start_new and event_end == event_end_new:
                    overlap_texts.append(overlap_texts_format_string.format(summary, event_start, event_end))

                if has_overlap(event_start, event_end, event_start_new, event_end_new):
                    overlap_text = overlap_texts_format_string.format(summary, event_start, event_end)
                    overlap_texts.append(overlap_text)

                if has_overlap(event_start, event_end, event_start_new, event_end_new):
                    overlap_text = overlap_texts_format_string.format(summary, event_start, event_end)
                    overlap_texts.append(overlap_text)

        if len(overlap_texts) > 0:
            ovarlaps_joined = ''.join(overlap_texts)                
            res +=  'Overlaps with: \n {texts}.'.format(texts=ovarlaps_joined)

    event = {
      'summary': event_text,
      # 'location': '800 Howard St., San Francisco, CA 94103',
      # 'description': 'A chance to hear more about Google\'s developer products.',
      'start': {
        'dateTime':  datetime_to_rfc(event_start_new),
        # 'timeZone': tz,
      },
      'end': {
        'dateTime': datetime_to_rfc(event_end_new),
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

    event = service.events().insert(calendarId=primary_calendar, body=event).execute()
    

    return event, res
    