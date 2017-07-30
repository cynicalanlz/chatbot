import flask
import pytest

from service.api import api
import aiohttp

@pytest.fixture()
def client(request):
    app = flask.Flask(__name__)
    app.register_blueprint(api)
    client = app.test_client()
    yield client


def test_bad_request(client):
    response = client.get('/')
    assert response.status_code == 404


def test_ai(client):
    response = client.post('/api/v1/get_ai_response', data={'slid': 'U5ZCR2NTH', 'msg': 'hi'}, follow_redirects=True)
    assert response.status_code == 200