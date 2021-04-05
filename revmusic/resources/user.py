from revmusic import db
from revmusic.constants import *
from revmusic.models import User, Album, Review, Tag
from revmusic.utils import is_valid_email, is_valid_pwd
from revmusic.mason import create_error_response, RevMusicBuilder
from flask_restful import Resource
from flask import Response, request, url_for
from sqlalchemy.exc import IntegrityError, StatementError
import re
import json
from jsonschema import validate, ValidationError


class UserCollection(Resource):
    def get(self):
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control_users_all('self')
        body.add_control_reviews_all()
        body.add_control_albums_all()
        body.add_control_add_user()

        body['items'] = []
        for user in User.query.all():
            item = RevMusicBuilder(
                username=user.username
            )
            item.add_control('self', url_for('api.useritem', user=user.username))
            item.add_control('profile', USER_PROFILE)
            body['items'].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(
                415, 'Unsupported media type',
                'Use JSON'
            )
        try:
            validate(request.json, User.get_schema())
        except ValidationError as e:
            return create_error_response(400, 'Invalid JSON document', str(e))
        
        username = request.json['username'].lower() # Lowercase the username
        email = request.json['email']
        password = request.json['password']

        # Validate email
        if not is_valid_email(email):
            return create_error_response(400, 'Invalid email format',
            'Use a proper email format')
        # Check that username not taken
        if User.query.filter_by(username=username).count() > 0:
            return create_error_response(409, 'Username already exists',
            'Username {} already exists'.format(username))
        # Check that email not taken
        if User.query.filter_by(email=email).count() > 0:
            return create_error_response(409, 'Email already exists',
            'Email {} already in use'.format(email))
        # Check that password has correct length
        if not is_valid_pwd(password):
            return create_error_response(400, 'Invalid password',
            'Password doesn\'t seem to have correct format')

        # Create the new user entry
        user = User(
            username=username,
            email=email,
            password=password
        )
        # Attempt to add to database
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(409, 'User already exists',
            'This user already seems to exist. Could also be that something went horribly wrong during committing to the db :D')
        # Respond to successful request
        return Response(status=201, headers={
            'Location': url_for('api.useritem', user=username)
        })

class UserItem(Resource):
    def get(self, user):
        db_user = User.query.filter_by(username=user).first()
        # Check that the requested user exists
        if not db_user:
            return create_error_response(
                404, 'User not found',
                'Yoooo, this user not here. Look somewhere else'
            )
        body = RevMusicBuilder(
            username=db_user.username,
            email=db_user.email
        )
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.useritem', user=db_user.username))
        body.add_control('profile', USER_PROFILE)
        body.add_control_users_all('collection')
        body.add_control_reviews_by(user)
        body.add_control_edit_user(user)
        body.add_control_delete_user(user)
        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, user):
        db_user = User.query.filter_by(username=user).first()
        # Check that the requested user exists
        if not db_user:
            return create_error_response(
                404, 'User not found',
                'Yoooo, this user not here. Look somewhere else'
            )
        if not request.json:
            return create_error_response(
                415, 'Unsupported media type',
                'Use JSON'
            )
        try:
            validate(request.json, User.get_schema())
        except ValidationError as e:
            return create_error_response(400, 'Invalid JSON document', str(e))
        
        username = request.json['username'].lower() # Lowercase the username
        email = request.json['email']
        password = request.json['password']

        # Check that possible new username is not taken
        if username != user:
            if User.query.filter_by(username=username).count() > 0:
                return create_error_response(409, 'Username already exists',
                'Username {} already exists'.format(username))
        # Validate email
        if not is_valid_email(email):
            return create_error_response(400, 'Invalid email format',
            'Use a proper email format')
        # Check that possible new email is not taken
        if email != db_user.email:
            if User.query.filter_by(email=email).count() > 0:
                return create_error_response(409, 'Email already exists',
                'Email {} already in use'.format(email))
        # Validate password
        if not is_valid_pwd(password):
            return create_error_response(400, 'Invalid password',
            'Password doesn\'t seem to have correct format')
        
        # Updated user entry
        db_user.username = username
        db_user.email = email
        db_user.password = password
        # Commit changes
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(409, 'Something went wrong',
            'Something went wrong while attempting to commit to db. This is probably a catastrophic situation 0.0. Don\' abuse it please')
        return Response(status=204)

    def delete(self, user):
        db_user = User.query.filter_by(username=user).first()
        # Check that the requested user exists
        if not db_user:
            return create_error_response(
                404, 'User not found',
                'Yoooo, this user not here. Look somewhere else'
            )
        db.session.delete(db_user)
        db.session.commit()
        return Response(status=204)
