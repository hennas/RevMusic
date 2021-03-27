from revmusic.constants import *
from revmusic.models import User, Album, Review, Tag
from revmusic.mason import create_error_response, RevMusicBuilder
from flask_restful import Resource
from flask import Response, request, url_for
import json


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
        pass

class UserItem(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass
