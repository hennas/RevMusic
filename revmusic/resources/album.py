from revmusic.constants import *
from revmusic.models import User, Album, Review, Tag
from revmusic.mason import create_error_response, RevMusicBuilder
from flask_restful import Resource
from flask import Response, request, url_for
import json


class AlbumCollection(Resource):
    def get(self):
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.albumcollection'))
        body.add_control_users_all()
        body.add_control_reviews_all()
        body.add_control_add_album()
        
        body['items'] = []
        for album in Album.query.all():
            item = RevMusicBuilder(
                unique_name=album.unique_name,
                title=album.title,
                artist=album.artist,
                release=album.publication_date.strftime('%Y-%m-%d'),
                duration=album.duration.strftime('%H:%M:%S'),
                genre=album.genre
            )
            item.add_control('self', url_for('api.albumitem', album=album.unique_name))
            item.add_control('profile', ALBUM_PROFILE)
            body['items'].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        pass

class AlbumItem(Resource):
    def get(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass
