from revmusic import db
from revmusic.constants import *
from revmusic.models import User, Album, Review, Tag
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
        body.add_control('self', url_for('api.usercollection'))
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
        # Source: https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
        regex = r'^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'
        if not re.search(regex, email):
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
        if len(password) is not 64:
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
        body.add_control('collection', url_for('api.usercollection'), title='All users')
        # TODO: ADD REVMUSIC:REVIEWS-BY
        # TODO: ADD REVMUSIC:TAGS-BY (IF WE DECIDE TO IMPLEMENT THEM)
        # TODO: ADD EDIT
        # TODO: ADD DELETE
        return Response(json.dumps(body), 200, mimetype=MASON)


    def put(self):
        pass

    def delete(self):
        pass
