from revmusic.constants import *
from revmusic.models import User, Album, Review, Tag
from revmusic.mason import create_error_response, RevMusicBuilder
from flask_restful import Resource, reqparse
from flask import Response, request, url_for
from sqlalchemy import func
import datetime
import json


class ReviewCollection(Resource):
    def __init__(self):
        """
        This enables the optional arguments for the GET request
        """
        self.parse = reqparse.RequestParser()
        self.parse.add_argument('filterby', type=str, required=False, choices=('album', 'artist', 'genre', 'user')) # TODO: default='album'? Could be handled so that if searchword is given, but there is no filterby, then just use 'album'
        self.parse.add_argument('searchword', type=str, required=False)
        self.parse.add_argument('timeframe', type=str, required=False)
        self.parse.add_argument('nlatest', type=int, required=False)

    def get(self):
        """
        Return reviews and handle filtering based on parameters given by the client
        """
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control_reviews_all('self')
        body.add_control_users_all()
        body.add_control_albums_all()

        # Obtain arguments sent by user
        args = self.parse.parse_args()
        reviews = []
        foreign_keys = []
        timeframe = []
        nlatest = args['nlatest'] # None or int

        if args['timeframe'] is not None:
            try:
                temp = args['timeframe'].split('_')
                timeframe.append('{}-{}-{}'.format(temp[0][4:], temp[0][2:4], temp[0][0:2]))
                # Check for possible second time
                if len(temp) is 2:
                    timeframe.append('{}-{}-{}'.format(temp[1][4:], temp[1][2:4], temp[1][0:2]))
                # Make sure no more than 2 timeframes were provided
                if len(temp) > 2:   
                    raise Exception('More than two timeframe parameters')
            except Exception as e:
                # Return an error if an exception occurred
                # TODO: CHECK ERROR NUMBER
                print(e)
                return create_error_response(415, 'Incorrect timeframe format', 'You provided an incorrect timeframe format. Please fix that >:(')

        # Error handling for nlatest is implemented by flask, since the type has been set to int
        
        # Handle filtering
        # NOTE: checking could also be based on searchword, if it is given, then check filterby (if not given use 'album'), otherwise just filter based on time
        if not args['filterby']:
            # No filterby
            if len(timeframe) < 1:
                # No timeframe provided, return all or nlatest
                reviews = Review.query.order_by(Review.submission_date.desc()).limit(nlatest).all()
            elif len(timeframe) == 1:
                # One time provided, return all or nlatest after that 
                reviews = Review.query.filter(func.date(Review.submission_date) >= timeframe[0])\
                    .order_by(Review.submission_date.desc()).limit(nlatest).all()
            else:
                # Two times provided, return all or nlatest between them
                reviews = Review.query.filter(func.date(Review.submission_date) >= timeframe[0])\
                    .filter(func.date(Review.submission_date) <= timeframe[1]).order_by(Review.submission_date.desc()).limit(nlatest).all()
    
        else:
            # Filterby provided, ensure that a searchword is also used
            if args['filterby'] and not args['searchword']:
                return create_error_response(415, 'Searchword required', 'If you using filterby, provide a searchword')

            # Handle filtering
            if args['filterby'] == 'album':
                foreign_keys = Album.query.filter(Album.title.contains(args['searchword'])).all()
            elif args['filterby'] == 'artist':
                foreign_keys = Album.query.filter(Album.artist.contains(args['searchword'])).all()
            elif args['filterby'] == 'genre':
                foreign_keys = Album.query.filter(Album.genre.contains(args['searchword'])).all()
            else: # Filter by users
                foreign_keys = User.query.filter(User.username.contains(args['searchword'])).all()

            if len(timeframe) < 1:
                reviews = Review.query.filter(Review.album_id.in_([fk.id for fk in foreign_keys])).order_by(Review.submission_date.desc()).limit(nlatest).all()
            elif len(timeframe) == 1:
                reviews = Review.query.filter(Review.album_id.in_([fk.id for fk in foreign_keys])).filter(func.date(Review.submission_date) >= timeframe[0])\
                    .order_by(Review.submission_date.desc()).limit(nlatest).all()
            else:
                reviews = Review.query.filter(Review.album_id.in_([fk.id for fk in foreign_keys])).filter(func.date(Review.submission_date) >= timeframe[0])\
                    .filter(func.date(Review.submission_date) <= timeframe[1]).order_by(Review.submission_date.desc()).limit(nlatest).all()

        body['items'] = []
        for review in reviews:
            item = RevMusicBuilder(
                identifier=review.identifier,
                user=review.user.username,
                album=review.album.title,
                title=review.title,
                star_rating=review.star_rating,
                submission_date=datetime.datetime.strftime(review.submission_date, '%Y-%m-%d %H:%M:%S')
            )
            item.add_control('self', url_for('api.reviewitem', album=review.album.unique_name, review=review.identifier))
            item.add_control('profile', REVIEW_PROFILE)
            body['items'].append(item)
        return Response(json.dumps(body), 200, mimetype=MASON)

class ReviewsByAlbum(Resource):
    def get(self, album):
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.reviewsbyalbum', album=album))
        body.add_control('up', url_for('api.albumitem', album=album), title='Album item for which the reviews have been submitted')
        body.add_control_reviews_all()
        body.add_control_add_review()
        
        reviews = Review.query.filter(Review.album == album_item).order_by(Review.submission_date.desc()).all()
        body['items'] = []
        for review in reviews:
            item = RevMusicBuilder(
                identifier=review.identifier,
                user=review.user.username,
                title=review.title,
                star_rating=review.star_rating,
                submission_date=datetime.datetime.strftime(review.submission_date, '%Y-%m-%d %H:%M:%S')
            )
            item.add_control('self', url_for('api.reviewitem', album=album, review=review.identifier))
            item.add_control('profile', REVIEW_PROFILE)
            body['items'].append(item)
            
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, album):
        pass

class ReviewsByUser(Resource):
    def get(self, user):
        user_item = User.query.filter_by(username=user).first()
        if not user_item:
            return create_error_response(404, 'User not found')
        
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.reviewsbyuser', user=user))
        body.add_control('up', url_for('api.useritem', user=user), title='User by whom the reviews have been submitted')
        body.add_control_reviews_all()
        
        reviews = Review.query.filter(Review.user == user_item).order_by(Review.submission_date.desc()).all()
        body['items'] = []
        for review in reviews:
            item = RevMusicBuilder(
                identifier=review.identifier,
                album=review.album.title,
                title=review.title,
                star_rating=review.star_rating,
                submission_date=datetime.datetime.strftime(review.submission_date, '%Y-%m-%d %H:%M:%S')
            )
            item.add_control('self', url_for('api.reviewitem', album=review.album.unique_name, review=review.identifier))
            item.add_control('profile', REVIEW_PROFILE)
            body['items'].append(item)
            
        return Response(json.dumps(body), 200, mimetype=MASON)
    
class ReviewItem(Resource):
    def get(self, album, review):
        pass

    def put(self, album, review):
        pass

    def delete(self, album, review):
        pass
