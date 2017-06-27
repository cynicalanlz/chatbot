from flask import Flask

from service.api import api, base


app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(base, url_prefix='')
