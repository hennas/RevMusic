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
                'The release date you provided is an invalid date')
        duration = None
        if 'duration' in request.json:
            duration = to_time(request.json['duration'])
            if duration is None:# None returned in case of an error
                return create_error_response(400, 'Invalid duration',
                'The album duration you provided is an invalid time')
        genre = None
        if 'genre' in request.json:
            genre = request.json['genre']

        # Check that unique_name is not in use
        if Album.query.filter_by(unique_name=unique_name).count() > 0:
            return create_error_response(409, 'Already exists',
            'Unique name "{}" is already in use'.format(unique_name))

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
            db.session.rollback()
            return create_error_response(409, 'Already exists',
            'Album with title "{}" already exists with artist "{}"'.format(title, artist))

        return Response(status=201, headers={
            'Location': url_for('api.albumitem', album=unique_name)
        })

class AlbumItem(Resource):
    def get(self, album):
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        
        # Handle optional data (date and time objects to string)
        release = album_item.publication_date
        duration = album_item.duration
        if release:
            release = release.strftime('%Y-%m-%d')
        if duration:
            duration = duration.strftime('%H:%M:%S')
            
        body = RevMusicBuilder(
            unique_name=album,
            title=album_item.title,
            artist=album_item.artist,
            release=release,
            duration=duration,
            genre=album_item.genre
        )
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.albumitem', album=album))
        body.add_control('profile', ALBUM_PROFILE)
        body.add_control('collection', url_for('api.albumcollection'), title='All albums')
        body.add_control_reviews_for(album)
        body.add_control_edit_album(album)
        body.add_control_delete_album(album)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, album):
        if not request.json:
            return create_error_response(415, 'Unsupported media type', 'Use JSON')
        
        try:
            validate(request.json, Album.get_schema())
        except ValidationError as e:
            return create_error_response(400, 'Invalid JSON document', str(e))
        
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        
        unique_name = request.json['unique_name'].lower()
        title = request.json['title']
        artist = request.json['artist']
        
        # Handle optional arguments; will be set to null if not provided
        release = None
        if 'release' in request.json:
            release = to_date(request.json['release'])
            if release is None: # None returned in case of an error
                return create_error_response(400, 'Invalid release date',
                'The release date you provided is an invalid date')
        duration = None
        if 'duration' in request.json:
            duration = to_time(request.json['duration'])
            if duration is None: # None returned in case of an error
                return create_error_response(400, 'Invalid duration',
                'The album duration you provided is an invalid time')
        genre = None
        if 'genre' in request.json:
            genre = request.json['genre']

        # Check that unique_name is not in use in case that it is changed
        if unique_name != album and Album.query.filter_by(unique_name=unique_name).count() > 0:
            return create_error_response(409, 'Already exists',
            'Unique name "{}" is already in use'.format(unique_name))

        # Update album values and commit
        album_item.unique_name = unique_name,
        album_item.title = title,
        album_item.artist = artist,
        album_item.publication_date = release,
        album_item.duration = duration,
        album_item.genre = genre

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(409, 'Already exists',
            'Album with title "{}" already exists with artist "{}"'.format(title, artist))

        return Response(status=204)

    def delete(self, album):
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        
        db.session.delete(album_item)
        db.session.commit()
        return Response(status=204)
