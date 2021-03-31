from revmusic import db
from revmusic.utils import *
from revmusic.constants import *
from revmusic.models import User, Album, Review, Tag
from revmusic.mason import create_error_response, RevMusicBuilder
from flask_restful import Resource
from flask import Response, request, url_for
from sqlalchemy.exc import IntegrityError, StatementError
import json
from jsonschema import validate, ValidationError


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
            # Handle optional data
            release = album.publication_date
            duration = album.duration
            if release:
                release = release.strftime('%Y-%m-%d')
            if duration:
                duration = duration.strftime('%H:%M:%S')

            item = RevMusicBuilder(
                unique_name=album.unique_name,
                title=album.title,
                artist=album.artist,
                release=release,
                duration=duration,
                genre=album.genre
            )
            item.add_control('self', url_for('api.albumitem', album=album.unique_name))
            item.add_control('profile', ALBUM_PROFILE)
            body['items'].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(
                415, 'Unsupported media type',
                'Use JSON'
            )
        try:
            validate(request.json, Album.get_schema())
        except ValidationError as e:
            return create_error_response(400, 'Invalid JSON document', str(e))
        
        unique_name = request.json['unique_name'].lower()
        title = request.json['title']
        artist = request.json['artist']
        # Handle optional arguments
        release = None
        if 'release' in request.json:
            release = to_date(request.json['release'])
            if release is None: # None returned in case of an error
                return create_error_response(400, 'Invalid release date',
                'The release data you provided is an invalid date')
        duration = None
        if 'duration' in request.json:
            duration = to_time(request.json['duration'])
            if duration is None:# None returned in case of an error
                return create_error_response(400, 'Invalid duration',
                'The release duration you provided is an invalid date')
        genre = None
        if 'genre' in request.json:
            genre = request.json['genre']

        # Check that unique_name is not in use
        if Album.query.filter_by(unique_name=unique_name).count() > 0:
            return create_error_response(409, 'unique_name already exists',
            'This unique name is already in use')

        # Create album entry and commit
        album = Album(
            unique_name=unique_name,
            title=title,
            artist=artist,
            publication_date=release,
            duration=duration,
            genre=genre
        )
        try:
            db.session.add(album)
            db.session.commit()
        except IntegrityError:
            return create_error_response(409, 'Already exists',
            'An album with the same title-artist combo already exists')

        return Response(status=201, headers={
            'Location': url_for('api.albumitem', album=unique_name)
        })

class AlbumItem(Resource):
    def get(self, album):
        return Response(status=200)

    def put(self, album):
        return Response(status=204)

    def delete(self, album):
        return Response(status=204)
