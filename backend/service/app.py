from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from service.api import api
from service.shared.models import db
from service.config import config, google_config



app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = bool(config['SQLALCHEMY_TRACK_MODIFICATIONS'])
app.config['SQLALCHEMY_DATABASE_URI'] = config['SQLALCHEMY_DATABASE_URI']

app.register_blueprint(api, url_prefix='/api')
db.init_app(app)
