import os

config = os.environ

google_config_keys_map = {
    'client_id' : 'GOOGLE_API_OAUTH_CLIENT_ID',
    'client_secret': 'GOOGLE_API_OAUTH_CLIENT_SECRET',
    'scope' : 'GOOGLE_API_SCOPES',
    'redirect_uri' : 'GOOGLE_API_REDIRECT_URL',
}
google_config = { key: config[value_key] for key, value_key in google_config_keys_map.items() }
