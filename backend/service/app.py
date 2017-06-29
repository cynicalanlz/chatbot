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


# def create_app_tables():
#     app = flask.Flask("app")
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
#     app.register_blueprint(api)
#     db.init_app(app)
#     with app.app_context():
#         # Extensions like Flask-SQLAlchemy now know what the "current" app
#         # is while within this block. Therefore, you can now run........
#         db.create_all()

#     return app