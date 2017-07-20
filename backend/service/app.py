from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from service.api import api
from service.shared.models import db
from service.config import config, google_config

import logging
from logging.handlers import RotatingFileHandler
from time import strftime
import traceback



app = Flask(__name__)

LOG_FILENAME = 'app_access_logs.log'

app.logger.setLevel(logging.INFO) # use the native logger of flask

handler = logging.handlers.RotatingFileHandler(
    LOG_FILENAME,
    maxBytes=1024 * 1024 * 100,
    backupCount=20
    )


logger = logging.getLogger('tdm')
logger.setLevel(logging.ERROR)
logger.addHandler(handler)

fileHandler = RotatingFileHandler(LOG_FILENAME, maxBytes=20971520,
                                  backupCount=5, encoding='utf-8')
fileHandler.setLevel(logging.DEBUG)
filefmt = '%(asctime)s [%(filename)s:%(lineno)d] %(rid)s: %(message)s'
fileFormatter = logging.Formatter(filefmt)
fileHandler.setFormatter(fileFormatter)
app.logger.addHandler(fileHandler)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = bool(config['SQLALCHEMY_TRACK_MODIFICATIONS'])
app.config['SQLALCHEMY_DATABASE_URI'] = config['SQLALCHEMY_DATABASE_URI']

app.register_blueprint(api, url_prefix='/api')
db.init_app(app)
