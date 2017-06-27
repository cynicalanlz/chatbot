import os

config = os.environ
config_dict = {
	'GOOGLE_API_OAUTH_CLIENT_ID' : '843279895494-jmab67kl6pnhr26c52efvjetlkrofgvt.apps.googleusercontent.com',
	'GOOGLE_API_OAUTH_CLIENT_SECRET' : 'ovkEmYGc1sD9-XhPSaMD0v9Y',
	'GOOGLE_API_SCOPES' : 'https://www.googleapis.com/auth/calendar',
	'GOOGLE_API_REDIRECT_URL' : 'http://ec2-34-212-103-70.us-west-2.compute.amazonaws.com/api/v1/register_cb',		
}

config.update(config_dict)

google_config_keys_map = {
    'client_id' : 'GOOGLE_API_OAUTH_CLIENT_ID',
    'client_secret': 'GOOGLE_API_OAUTH_CLIENT_SECRET',
    'scope' : 'GOOGLE_API_SCOPES',
    'redirect_uri' : 'GOOGLE_API_REDIRECT_URL',
}
google_config = { key: config[value_key] for key, value_key in google_config_keys_map.items() }
