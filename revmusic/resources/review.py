from revmusic import db
from revmusic.constants import *
from revmusic.models import User, Album, Review, Tag
from revmusic.mason import create_error_response, RevMusicBuilder
from revmusic.utils import create_identifier
from flask_restful import Resource, reqparse
from flask import Response, request, url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, StatementError
import datetime
import json
from jsonschema import validate, ValidationError


class ReviewCollection(Resource):
    def __init__(self):
        """
        This enables the optional query parameters for the GET request
        """
        self.parse = reqparse.RequestParser()
        self.parse.add_argument('filterby', type=str, required=False, choices=('album', 'artist', 'genre', 'user'))
        self.parse.add_argument('searchword', type=str, required=False)
        self.parse.add_argument('timeframe', type=str, required=False)
        self.parse.add_argument('nlatest', type=int, required=False)

    def get(self):
        """
        Responds to GET request with a listing of review items known to the API (JSON document with added hypermedia controls (MASON))
        Query parameters in the request URL can be used to filter the returned reviews.
        """
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control_reviews_all('self')
        body.add_control_users_all()
        body.add_control_albums_all()

        # Obtain query parameters sent by user
        args = self.parse.parse_args()
        reviews = []
        foreign_keys = []
        timeframe = []
        nlatest = args['nlatest'] # None or int
        
        try:
            validate(json.loads(args), REVIEW_ALL_SCHEMA )
        except ValidationError as e:
            return create_error_response(400, 'Invalid query parameters provided', str(e))
        
        if args['timeframe'] is not None:
            try:
                temp = args['timeframe'].split('_')
                if not temp[0][4:].isnumeric() or not temp[0][2:4].isnumeric() or not temp[0][0:2].isnumeric():
                    return create_error_response(415, 'Incorrect timeframe format', 'You provided an incorrect timeframe format. Please fix that >:(')
                timeframe.append('{}-{}-{}'.format(temp[0][4:], temp[0][2:4], temp[0][0:2]))
                # Check for possible second time
                if len(temp) is 2:
                    if not temp[1][4:].isnumeric() or not temp[1][2:4].isnumeric() or not temp[1][0:2].isnumeric():
                        return create_error_response(415, 'Incorrect timeframe format', 'You provided an incorrect timeframe format. Please fix that >:(')
                    timeframe.append('{}-{}-{}'.format(temp[1][4:], temp[1][2:4], temp[1][0:2]))
                # Make sure no more than 2 timeframes were provided
                if len(temp) > 2:   
                    raise Exception('More than two timeframe parameters')
            except Exception as e:
                # Return an error if an exception occurred
                return create_error_response(415, 'Incorrect timeframe format', 'You provided an incorrect timeframe format. Please fix that >:( {}'.format(e))

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
        """
        Responds to GET request with a listing of all reviews for the specified album (JSON document with added hypermedia controls (MASON))
        If the specified album does not exist in the API, 404 error code returned.
        : param str album: the unique name of the album the reviews of which are requested, provided in the request URL
        """
        # Fetch the album item from the database and check whether it exists
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.reviewsbyalbum', album=album))
        body.add_control('up', url_for('api.albumitem', album=album), title='Album item for which the reviews have been submitted')
        body.add_control_reviews_all()
        body.add_control_add_review(album)
        
        # Fetch all the reviews from the database for the specified album
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
        """
        Responds to POST request by adding a new review item to the specified album's review collection.
        If no errors happens while adding the review, the location of the new item is returned in the 'Location' response header.
        Otherwise an appropriate error code with a human-readable error message is returned.
        : param str album: the unique name of the album to which a new review is added, provided in the request URL
        """
        if not request.json:
            return create_error_response(415, 'Unsupported media type', 'Use JSON')
        try:
            validate(request.json, Review.get_schema())
        except ValidationError as e:
            return create_error_response(400, 'Invalid JSON document', str(e))
        
        # Does the album for which the review is being submitted exist
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        
        # Create an unique identifier and get the submission datetime for the review
        # Note: the probability of creating an identifier that already exist is practically zero, 
        # but just to be absolutely sure the creation is tried until unique identifier is created. 
        # Infinite looping extremely unlikely.
        while True:
            identifier, submission_dt = create_identifier('review_')
            if Review.query.filter_by(identifier=identifier).count() == 0:
                break
            
        # Get the arguments from the request
        user = request.json['user'].lower() # Lowercase just in case
        title = request.json['title']
        content = request.json['content']
        star_rating = request.json['star_rating']
        
        # Does the user by which the review is being submitted exist (provided in the request body)
        user_item = User.query.filter_by(username=user).first()
        if not user_item:
            return create_error_response(404, 'User not found')

        # Create a new review entry
        review = Review(
            identifier=identifier,
            user=user_item,
            album=album_item,
            title=title,
            content=content,
            star_rating=star_rating,
            submission_date=submission_dt
        )

        # Attempt to add to database
        try:
            db.session.add(review)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(409, 'Already exists',
            'User "{}" has already submitted a review to album with title "{}"'.format(user, album_item.title))
        
        # Respond to successful request
        return Response(status=201, headers={
            'Location': url_for('api.reviewitem', album=album, review=identifier) # The location of the added item
        })

class ReviewsByUser(Resource):
    def get(self, user):
        """
        Responds to GET request with a listing of all reviews submitted by the specified user (JSON document with added hypermedia controls (MASON))
        If the specified user does not exist in the API, 404 error code returned.
        : param str user: the username of the user whose reviews are requested, provided in the request URL
        """
        # Fetch the user item from the database and check if it exists
        user_item = User.query.filter_by(username=user).first()
        if not user_item:
            return create_error_response(404, 'User not found')
        
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.reviewsbyuser', user=user))
        body.add_control('up', url_for('api.useritem', user=user), title='User by whom the reviews have been submitted')
        body.add_control_reviews_all()
        
        # Fetch the reviews from the database submitted by the specified user
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
        """
        Responds to GET request with the representation of the requested review item (JSON document with added hypermedia controls (MASON))
        If the requested review or the album for which the review should have been submitted does not exist in the API, 404 error code returned.
        : param str album: the unique name of the album for which the requested review have been submitted, provided in the request URL
        : param str review: the identifier of the requested review, provided in the request URL
        """
        # Fetch the album and review items from the database and check if they exist
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        review_item = Review.query.filter(Review.identifier == review).filter(Review.album == album_item).first()
        if not review_item:
            return create_error_response(404, 'Review not found')
        
        # Create response
        user = review_item.user.username
        body = RevMusicBuilder(
            identifier=review,
            user=user,
            album=album_item.title,
            artist=album_item.artist,
            title=review_item.title,
            content=review_item.content,
            star_rating=review_item.star_rating,
            submission_date=datetime.datetime.strftime(review_item.submission_date, '%Y-%m-%d %H:%M:%S')
        )
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control('self', url_for('api.reviewitem', album=album, review=review))
        body.add_control('profile', REVIEW_PROFILE)
        body.add_control('author', url_for('api.useritem', user=user), title='The user who has submitted the review')
        body.add_control('about', url_for('api.albumitem', album=album), title='The album for which the review has been written')
        body.add_control_reviews_by(user)
        body.add_control_reviews_for(album)
        body.add_control_reviews_all()
        body.add_control_edit_review(album, review)
        body.add_control_delete_review(album, review)
        
        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, album, review):
        """
        Responds to PUT request by replacing the review item's representation with the provided new one. 
        If an error happens while handling the request, an appropriate error code with a human-readable error message is returned.
        : param str album: the unique name of the album for which the requested review have been submitted, provided in the request URL
        : param str review: the identifier of the requested review, provided in the request URL
        """
        if not request.json:
            return create_error_response(415, 'Unsupported media type', 'Use JSON')
        try:
            validate(request.json, Review.get_schema())
        except ValidationError as e:
            return create_error_response(400, 'Invalid JSON document', str(e))
        
        # Fetch the album and review items from the database and check if they exist
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        review_item = Review.query.filter(Review.identifier == review).filter(Review.album == album_item).first()
        if not review_item:
            return create_error_response(404, 'Review not found')
        
        # Create an updated unique identifier and get the updated submission datetime for the review
        # Note: the probability of creating an identifier that already exist is practically zero, 
        # but just to be absolutely sure the creation is tried until unique identifier is created. 
        # Infinite looping extremely unlikely.
        while True:
            identifier, submission_dt = create_identifier('review_')
            if Review.query.filter_by(identifier=identifier).count() == 0:
                break
        original_user = review_item.user.username
        # Get the arguments from the request
        user = request.json['user'].lower() # Lowercase just in case
        title = request.json['title']
        content = request.json['content']
        star_rating = request.json['star_rating']
        
        # Check whether provided user in the request matches the current writer of the review
        if user != original_user:
            return create_error_response(409, 'Username does not match', 
            'Provided user "{}" has not submitted this review'.format(user))
        
        # Update review values and commit
        review_item.identifier = identifier
        review_item.title = title
        review_item.content = content
        review_item.star_rating = star_rating
        review_item.submission_date = submission_dt

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return create_error_response(409, 'Unexpected conflict',
            'An unexpected conflict happened while committing to the database')
        
        return Response(status=204, headers={
            'Location': url_for('api.reviewitem', album=album, review=identifier) # The location of the updated item
        })

    def delete(self, album, review):
        """
        Responds to DELETE request by deleting the requested review item.
        If the requested review or the album for which the review should have been submitted does not exist in the API, 404 error code returned.
        : param str album: the unique name of the album for which the requested review have been submitted, provided in the request URL
        : param str review: the identifier of the requested review, provided in the request URL
        """
        # Fetch the album and review items from the database and check if they exist
        album_item = Album.query.filter_by(unique_name=album).first()
        if not album_item:
            return create_error_response(404, 'Album not found')
        review_item = Review.query.filter(Review.identifier == review).filter(Review.album == album_item).first()
        if not review_item:
            return create_error_response(404, 'Review not found')
        
        db.session.delete(review_item)
        db.session.commit()
        return Response(status=204)
