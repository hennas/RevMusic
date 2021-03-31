import os
import re
import json
import time
import pytest
import tempfile
import datetime
from jsonschema import validate
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

def _get_user_json(user='itsame', email='itm@gmail.com', pwd='9294ab38039f60d2ec53822fb46b52c663af7ea478f4d17bf43da44ede5e166c'):
    """
    Returns json for a user.
    """
    return {
        "username": user,
        "email": email,
        "password": pwd
    }

def _get_album_json(unique_name='test', title='Test', artist='Tester', release='2001-04-25', duration='00:44:35', genre='Test Metal'):
    """
    Returns json for a album.
    """
    return {
        "unique_name": unique_name,
        "title": title,
        "artist": artist,
        "release": release,
        "duration": duration,
        "genre": genre
    }

def _check_namespace(client, body):
    """
    Checks that the 'revmusic' namespace is found in the given response
    and that the 'name' is included and accessable
    """
    assert '@namespaces' in body
    assert 'revmusic' in body['@namespaces']
    assert 'name' in body['@namespaces']['revmusic']
    ns_href = body['@namespaces']['revmusic']['name']
    resp = client.get(ns_href)
    assert resp.status_code == 200

def _check_control_present(client, body, ctrl):
    """
    Checks that the given control is present in the message body. Includes href checking
    """
    assert '@controls' in body
    assert ctrl in body['@controls']
    assert 'href' in body['@controls'][ctrl]

def _check_control_get_method(client, body, ctrl):
    """
    Check that the given control is found in the message body and 
    is accessable
    """
    _check_control_present(client, body, ctrl)
    resp = client.get(body['@controls'][ctrl]['href'])
    assert resp.status_code == 200

def _check_control_post_method(client, body, ctrl, data):
    """
    Check that the given control is correct
    """
    _check_control_present(client, body, ctrl)
    ctrl_obj = body['@controls'][ctrl]
    href = ctrl_obj['href']
    method = ctrl_obj['method'].lower()
    encoding = ctrl_obj['encoding'].lower()
    schema = ctrl_obj['schema']
    assert method == 'post'
    assert encoding == 'json'
    validate(data, schema)
    resp = client.post(href, json=data)
    assert resp.status_code == 201

def _check_control_delete_method(client, body, ctrl):
    """
    Check that the given control works correctly
    """
    _check_control_present(client, body, ctrl)
    href = body['@controls'][ctrl]['href']
    method = body['@controls'][ctrl]['method'].lower()
    assert method == 'delete'
    resp = client.delete(href)
    assert resp.status_code == 204

def _check_control_put_method(client, body, ctrl):
    """
    Check that the given control works correctly
    """
    _check_control_present(client, body, ctrl)
    ctrl_obj = body['@controls'][ctrl]
    href = ctrl_obj['href']
    method = ctrl_obj['method'].lower()
    encoding = ctrl_obj['encoding'].lower()
    schema = ctrl_obj['schema']
    assert method == 'put'
    assert encoding == 'json'
    body = _get_user_json(user=body['username'])
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204

#######
# TESTS
#######
class TestEntryPoint(object):
    RESOURCE_URL = '/api/'

    def test_get(self, client):
        print('\n==================RUNNING API TESTS===================')
        print('Testing GET for EntryPoint: ', end='')
        # Check that request works properly, i.e. return 200
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        # Check that everything that should be included, is included
        body = json.loads(resp.data)
        # Check namespace
        _check_namespace(client, body)
        # Check included controls
        _check_control_get_method(client, body, 'revmusic:reviews-all')
        _check_control_get_method(client, body, 'revmusic:albums-all')
        _check_control_get_method(client, body, 'revmusic:users-all')


class TestUserCollection(object):
    RESOURCE_URL = '/api/users/'
    INVALID_URL = '/api/userss/'
    RESOURCE_NAME = 'UserCollection'

    def test_get(self, client):
        print('\nTesting GET for {}: '.format(self.RESOURCE_NAME), end='')
        # Check that request works properly, i.e. return 200
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        # Check that everything that should be included, is included
        body = json.loads(resp.data)
        # Check namespace
        _check_namespace(client, body)
        # Check included controls
        _check_control_get_method(client, body, 'self')
        _check_control_get_method(client, body, 'revmusic:albums-all')
        _check_control_get_method(client, body, 'revmusic:reviews-all')
        _check_control_post_method(client, body, 'revmusic:add-user', _get_user_json())

        # Check that the 2 test users are found
        assert len(body['items']) == 2
        # Check that the required info is provided for items
        for item in body['items']:
            assert 'username' in item
            _check_control_get_method(client, item, 'profile')
            _check_control_get_method(client, item, 'self')

        # Invalid URL
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_valid_post(self, client):
        print('\nTesting valid POST for {}: '.format(self.RESOURCE_NAME), end='')
        user = _get_user_json()
        # Check that a valid resonse succseed
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 201
        # Check that the headers is correct
        assert resp.headers['Location'].endswith(self.RESOURCE_URL + user['username'] + '/')
        # Check that the user was actually added
        resp = client.get(resp.headers['Location'])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body['username'] == user['username']
        assert body['email'] == user['email']

    def test_wrong_mediatype_post(self, client):
        print('\nTesting wrong mediatype POST for {}: '.format(self.RESOURCE_NAME), end='')
        user = _get_user_json()
        resp = client.post(self.RESOURCE_URL, data=json.dumps(user))
        assert resp.status_code == 415

    def test_missing_post(self, client):
        print('\nTesting missing info POST for {}: '.format(self.RESOURCE_NAME), end='')
        # Missing username
        user = _get_user_json()
        del user['username']
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400
        # Missing email
        user = _get_user_json()
        del user['email']
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400
        # Missing password
        user = _get_user_json()
        del user['password']
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

    def test_incorrect_post(self, client):
        print('\nTesting invalid values POST for {}: '.format(self.RESOURCE_NAME), end='')
        # Invalid email
        user = _get_user_json(email='a')
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(email='a@a')
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(email='a@a.')
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(email='@a.com')
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        # Invalid password
        user = _get_user_json()
        user = _get_user_json(pwd='a'*65)
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(pwd='a'*6)
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        # Invalid URL
        user = _get_user_json()
        resp = client.post(self.INVALID_URL, json=user)
        assert resp.status_code == 404

    def test_already_exists_post(self, client):
        print('\nTesting already exists POST for {}: '.format(self.RESOURCE_NAME), end='')
        user = _get_user_json()
        resp = client.post(self.RESOURCE_URL, json=user)
        # Try to re-register same user
        resp = client.post(self.RESOURCE_URL, json=user)
        assert resp.status_code == 409


class TestUserItem(object):
    RESOURCE_URL = '/api/users/admin/'
    INVALID_URL = '/api/users/swag_xd/'
    RESOURCE_NAME = 'UserItem'

    def test_get(self, client):
        print('\nTesting GET for {}: '.format(self.RESOURCE_NAME), end='')
        # Check that request works properly, i.e. return 200
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        # Check that everything that should be included, is included
        body = json.loads(resp.data)
        # Check namespace
        _check_namespace(client, body)
        # Check included controls
        _check_control_get_method(client, body, 'self')
        _check_control_get_method(client, body, 'profile')
        _check_control_get_method(client, body, 'collection')
        _check_control_get_method(client, body, 'revmusic:reviews-by')
        _check_control_put_method(client, body, 'edit')
        _check_control_delete_method(client, body, 'revmusic:delete')
        # Check that user info is included
        assert body['username'] == 'admin'
        assert body['email'] == 'root@admin.com'
        # Also test an invalid UserItem url
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_valid_put(self, client):
        print('\nTesting valid PUT for {}: '.format(self.RESOURCE_NAME), end='')
        # Check that request works properly, i.e. return 200
        user = _get_user_json()
        # Check that a valid resonse succseed
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 204
        # Check that the info was actually updated
        resp = client.get('/api/users/itsame/')
        assert resp.status_code == 200
        body = json.loads(resp.data) 
        assert body['username'] == user['username']
        assert body['email'] == user['email']

    def test_wrong_mediatype_put(self, client):
        print('\nTesting wrong mediatype PUT for {}: '.format(self.RESOURCE_NAME), end='')
        user = _get_user_json()
        resp = client.put(self.RESOURCE_URL, data=json.dumps(user))
        assert resp.status_code == 415

    def test_missing_put(self, client):
        print('\nTesting missing info PUT for {}: '.format(self.RESOURCE_NAME), end='')
        # Missing username
        user = _get_user_json()
        del user['username']
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400
        # Missing email
        user = _get_user_json()
        del user['email']
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400
        # Missing password
        user = _get_user_json()
        del user['password']
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

    def test_incorrect_put(self, client):
        print('\nTesting invalid values PUT for {}: '.format(self.RESOURCE_NAME), end='')
        # Invalid email
        user = _get_user_json(email='a')
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(email='a@a')
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(email='a@a.')
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(email='@a.com')
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        # Invalid password
        user = _get_user_json()
        user = _get_user_json(pwd='a'*65)
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        user = _get_user_json(pwd='a'*6)
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 400

        # Invalid URL
        user = _get_user_json()
        resp = client.put(self.INVALID_URL, json=user)
        assert resp.status_code == 404

    def test_already_exists_put(self, client):
        print('\nTesting already exists PUT for {}: '.format(self.RESOURCE_NAME), end='')
        # Try to edit to existing username
        user = _get_user_json(user='YTC FAN')
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 409
        # Try to edit to existing email
        user = _get_user_json(user='admin', email='best_rapper@gmail.com')
        resp = client.put(self.RESOURCE_URL, json=user)
        assert resp.status_code == 409

    def test_delete(self, client):
        print('\nTesting delete PUT for {}: '.format(self.RESOURCE_NAME), end='')
        # Valid deletion
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        # Already deleted
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        # Invalid URL
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestUserCollection(object):
    RESOURCE_URL = '/api/albums/'
    INVALID_URL = '/api/albumss/'
    DATE_REGEX = r'^([0-9]{4}[-][0-9]{2}-[0-9]{2})$'
    DURATION_REGEX = r'^([0-9]{2}[:][0-9]{2}:[0-9]{2})$'
    RESOURCE_NAME = 'AlbumCollection'

    def test_get(self, client):
        print('\nTesting GET for {}: '.format(self.RESOURCE_NAME), end='')
        # Check that request works properly, i.e. return 200
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        # Check that everything that should be included, is included
        body = json.loads(resp.data)
        # Check namespace
        _check_namespace(client, body)
        # Check included controls
        _check_control_get_method(client, body, 'self')
        _check_control_get_method(client, body, 'revmusic:users-all')
        _check_control_get_method(client, body, 'revmusic:reviews-all')
        _check_control_post_method(client, body, 'revmusic:add-album', _get_album_json())

        # Check that the 3 test albums are found
        assert len(body['items']) == 3
        # Check that the required info is provided for items
        for item in body['items']:
            assert 'unique_name' in item
            assert 'title' in item
            assert 'artist' in item
            assert 'release' in item
            assert 'duration' in item
            assert 'genre' in item

            # Check that release and duration formats are correct, if they are not null
            if item['release']:
                assert re.search(self.DATE_REGEX, item['release'])
            if item['duration']:
                assert re.search(self.DURATION_REGEX, item['duration'])

            _check_control_get_method(client, item, 'profile')
            _check_control_get_method(client, item, 'self')

        # Invalid URL
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404
