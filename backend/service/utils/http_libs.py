import os, json, httplib2

config = os.environ

def get_url_json(url):

    hostname = ''.join([
        config['FLASK_PROTOCOL'],
        "://",
        config['FLASK_HOST']
    ])
    
    url = ''.join([
        hostname,
        url,
        ])

    h = httplib2.Http(".cache")

    (resp_headers, content) = h.request(url, "GET")    
    
    content = content.decode('utf-8')

    if content is None or not content:
        return {}

    try:
        jsn = json.loads(content)
    except:
        return {}

    return jsn
    

def get_user_google_auth(slid):
    """
    Gets user's calendar authentication
    
    @@params
    ----------
    slid : string
           slack team id

    """

    format_string = "/api/v1/get_user_google_auth?slid={}"
    url = format_string.format(slid)
    jsn = get_url_json(url)

    val = False

    if jsn:
        val = jsn.get('google_auth', False)

    return val

def check_auth(slid):
    auth = get_user_google_auth(slid) # get user google calendar auth
    message = False

    if not auth:
        message = """\
        Looks like you are not authorized. To authorize Google Calendar open this url in browser {}?slid={}&tid={}\
        """.format(config['GOOGLE_API_REDIRECT_URL'], slid, team)

    elif auth == 'multiple':
        message = """\
        Looks like you have multiple records for your id. Contact the app admin.\
        """

    return auth, message


def get_tokens():
    """
    Gets tokens via api    

    """

    jsn = get_url_json("/api/v1/get_tokens")

    tokens = []

    if jsn:        
        tokens = jsn['tokens']
    
    return set(tokens)

