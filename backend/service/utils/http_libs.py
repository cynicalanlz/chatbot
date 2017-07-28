import os, json, httplib2
import aiohttp
config = os.environ


async def get_url_json(url):

    hostname = ''.join([
        config['FLASK_PROTOCOL'],
        "://",
        config['FLASK_HOST']
    ])
    
    url = ''.join([
        hostname,
        url,
        ])

    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.github.com/events') as resp:
            if resp.status == 200:                
                return await resp.json()
            
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

    format_string = "/api/v1/get_ai_response?slid={}&msg={}"
    url = format_string.format(slid)
    jsn = await get_url_json(url)

    return jsn


async def get_tokens():
    """
    Gets tokens via api    

    """

    jsn = await get_url_json("/api/v1/get_tokens")

    tokens = []

    if jsn:        
        tokens = jsn['tokens']
    
    return set(tokens)

async def get_tokens(team):
    """
    Gets tokens via api    

    """

    jsn = await get_url_json("/api/v1/get_token?team={}".format(team))    

    if jsn:        
        token = jsn['token']    
        return token
    else:
        return False

