from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from service.api import api
from service.shared.models import db


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

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://tapdone3_user:09234ssds2e0mx4rqw8oe2nxq9w8643@tapdone.cznk1sm7ddt1.us-west-2.rds.amazonaws.com:5432/tapdone3_db'

app.register_blueprint(api, url_prefix='/api')

db.init_app(app)
