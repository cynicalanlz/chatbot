from flask import Flask
import pytest

from service.api import api


@pytest.fixture()
def client(request):
    app = Flask(__name__)
    app.register_blueprint(api)
    client = app.test_client()
    yield client


def test_bad_request(client):
    response = client.get('/')

    assert response.status_code == 404


def test_hello_world(client):
    response = client.get('/v1/hello')

    response_text = response.get_data(as_text=True)

    assert 'Hello' in response_text
    assert 'World' in response_text
