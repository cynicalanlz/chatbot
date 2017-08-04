import os, json, httplib2
import aiohttp
import logging

config = os.environ


async def add_flask_host(url):
    hostname = ''.join([
        config['FLASK_PROTOCOL'],
        "://",
        config['FLASK_HOST']
    ])
    
    url = ''.join([
        hostname,
        url,
        ])

    return url

async def get_url_json(url):

    url = await add_flask_host(url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:                
                resp = await resp.json()
                # logging.info(url)
                # logging.info(resp)
                return resp
            else:
                resp = {
                    'error' : resp.status
                }

async def post_url_json(url, jsn):

    url = await add_flask_host(url)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=jsn) as resp:            
            if resp.status == 200:
                resp = await resp.json()
                # logging.info(url)
                # logging.info(resp)
                return resp
            else:
                resp = {
                    'error' : resp.status
                }
            
async def get_user_google_auth(slid):
    """
    Gets user's calendar authentication
    
    @@params
    ----------
    slid : string
           slack team id

    """

    format_string = "/api/v1/get_user_google_auth?slid={}"
    url = format_string.format(slid)
    jsn = await get_url_json(url)

    val = False

    if jsn:
        val = jsn.get('google_auth', False)

    return val

async def get_ai_response(slid, msg):
    """
    Gets user's calendar authentication
    
    @@params
    ----------
    slid : string
           slack team id

    """
    in_jsn = {}
    in_jsn['slid'] = slid
    in_jsn['msg'] = msg
    url = "/api/v1/get_ai_response"
    out_jsn = await post_url_json(url, in_jsn)

    return out_jsn


async def get_tokens():
    """
    Gets tokens via api    

    """

    jsn = await get_url_json("/api/v1/get_tokens")

    tokens = []

    if jsn:        
        tokens = jsn['tokens']
    
    return tokens

async def get_token(team):
    """
    Gets tokens via api    

    """
    format_string = "/api/v1/get_token?team={}"
    url = format_string.format(team)
    jsn = await get_url_json(url)

    if jsn:        
        token = jsn['token']    
        return token
    else:
        return False

async def create_calendar_event(auth, event_text, event_start_time, event_end_time, event_date, speech):
    url = '/api/v1/create_calendar_event'
    
    in_jsn = {}
    in_jsn['auth'] = auth
    in_jsn['event_text'] = event_text
    in_jsn['event_start_time'] = event_start_time
    in_jsn['event_end_time'] = event_end_time
    in_jsn['event_date'] = event_date
    in_jsn['speech'] = speech
    api_resp = await post_url_json(url, in_jsn)

    if api_resp and 'response' in api_resp and 'event_link' in api_resp:
        user_response = api_resp['response']
        event_link = api_resp['event_link']
        return event_link, user_response
    else:
        return '', ''
