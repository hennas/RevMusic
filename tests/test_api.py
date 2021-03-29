import os
import json
import time
import pytest
import tempfile
import datetime
from urllib.parse import quote
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, StatementError

from revmusic import create_app, db
from revmusic.utils import to_date, to_time, to_datetime
from revmusic.models import User, Album, Review, Tag
from tests.populate_test_db import populate_db

# RUN WITH: $ python3 -m pytest -s tests
# The example python project provided by the course assistants was a basis for this
# URL: https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/tests/resource_test.py

@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()

@pytest.fixture
def client():
    """
    Setup the revmusic database for testing
    @pytest.fixture decoration ensures that all functions starting with test_ are run
    """
    # Configure the app
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "TESTING": True
    }
    # Create the app and add the configuration
    app = create_app(config)
    # Create the app's database
    with app.app_context():
        db.create_all()
        # Make sure the database gets populated before running tests
        if not populate_db(db):
            return
    # Provides the client for tests
    yield app.test_client()
    # Close the temp files
    os.close(db_fd)
    os.unlink(db_fname)

#######################
# Boilerplate functions
#######################

# TODO: ADD THE _get functions

def _get_user_json():
    return {
        "username": "itsame",
        "email": "itm@gmail.com",
        "password": "9294ab38039f60d2ec53822fb46b52c663af7ea478f4d17bf43da44ede5e166c"
    }

#######
# TESTS
#######
class TestEntryPoint(object):
    RESOURCE_URL = '/api/'

    def test_get(self, client):
        print('\n==================RUNNING API TESTS===================')
        print('Testing GET for EntryPoint...')
        # Check that request works properly, i.e. return 200
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        # Check that everything that should be included, is included
        body = json.loads(resp.data)
        # @Controls and @namespaces included
        keys = list(body.keys())
        assert '@namespaces' in keys
        assert '@controls' in keys
        # Check included controls
        assert 'revmusic:reviews-all' in body['@controls']
        assert 'revmusic:albums-all' in body['@controls']
        assert 'revmusic:users-all' in body['@controls']
 
class TestUserCollection(object):
    RESOURCE_URL = '/api/users/'

    def test_get(self, client):
        print('\nTesting GET for UserCollection...')
        # Check that request works properly, i.e. return 200
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        # Check that everything that should be included, is included
        body = json.loads(resp.data)
        # @Controls and @namespaces included
        keys = list(body.keys())
        assert '@namespaces' in keys
        assert '@controls' in keys
        # Check included controlsimport html
        assert 'self' in body['@controls']
        assert self.RESOURCE_URL in body['@controls']['self']['href']
        assert 'revmusic:albums-all' in body['@controls']
        assert 'revmusic:reviews-all' in body['@controls']
        # Check that the 2 test users are found
        assert len(body['items']) == 2
        # Check that the required info is provided for items
        for item in body['items']:
            assert 'username' in item
            assert '@controls' in item
            assert 'profile' in item['@controls']
            assert 'href' in item['@controls']['profile']
            assert '/profiles/user/' in item['@controls']['profile']['href']
            assert 'self' in item['@controls']
            assert 'href' in item['@controls']['self']
            # Test that user URL is formed correctly
            user = quote(item['username']) # encoding
            assert '/api/users/{}/'.format(user) == item['@controls']['self']['href']

    def test_valid_post(self, client):
        print('\nTesting valid POST for UserCollection...')
        user = _get_user_json()
        # Check that a valid resonse succseed
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 201
        # Check that the headers is correct
        assert resp.headers['Location'].endswith(self.RESOURCE_URL + user['name'] + '/')
        # Check that the user was actually added
        resp = client.get(resp.headers['Location'])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        print(body)





























class temp(object):
    RESOURCE_URL = '/api/'

    def test_a(self, client):
        assert 1 == 1

