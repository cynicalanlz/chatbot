import os

config = os.environ

google_config_keys_map = {
    'client_id' : 'GOOGLE_API_OAUTH_CLIENT_ID',
    'client_secret': 'GOOGLE_API_OAUTH_CLIENT_SECRET',
    'scope' : 'GOOGLE_API_SCOPES',
    'redirect_uri' : 'GOOGLE_API_REDIRECT_URL',
    'prompt' : 'GOOGLE_CONFIG_PROMT'
}
google_config = { key: config[value_key] for key, value_key in google_config_keys_map.items() }

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": '%(asctime)s [%(filename)s:%(lineno)d] : %(message)s'
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "slack_app.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": "slack_app_error.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        }
    },

    "loggers": {
        "aiohttp.access": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.client": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.internal": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.access": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.server": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aiohttp.web": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        },
        "aaiohttp.websocket": {
            "level": "DEBUG",
            "handlers": ["console", "info_file_handler"],
            "propagate": "no"
        }

    },

    "root": {
        "level": "INFO",
        "handlers": ["console", "info_file_handler", "error_file_handler"]
    }
}