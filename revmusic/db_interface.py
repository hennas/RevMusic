from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError

from . import db
from .models import User, Album, Review, Tag
from .utils import to_date


class DBInterface:
    """
    Provides functions related to interacting with the SQLAlchemy database
    """

    ##################
    # Adding to the DB
    ##################

    def db_add_user(username, email, password):
        """
        Used to add a new user to the database
        Params:
        - username: Unique name for the user
        - email: Unique e-mail address for the user
        - password: User's password as a SHA256 hash
        Returns: True if successful; False otherwise
        """
        print("Adding user {} to db".format(username))
        # Create the user entity
        user = User(
            username=username,
            email=email,
            password=password
        )
        # Attempt to add 
        if not DBInterface.commit_to_db(user):
            return False
        return True

    def db_add_album(title, artist, publication_date=None, duration=None, genre=None):
        """
        Used to add a new album to the database
        Params:
        - title: Album title
        - artist: Album's performer
        - publication_date: When the album was published dd-mm-YYYY (Can be empty)
        - duration: Album length in minutes (Can be empty)
        - genre: Album's genre (Can be empty)
        Returns: True if successful; False otherwise
        """
        print("Adding album \"{}\" from {} to db".format(title, artist))
        # If a date is provided, make sure its proper
        if publication_date is not None:
            publication_date = to_date(publication_date)
            if publication_date is None:
                return False
        # Create the album entity
        album = Album(
            title=title,
            artist=artist,
            publication_date=publication_date,
            duration=duration,
            genre=genre
        )
        # Attempt to add 
        if not DBInterface.commit_to_db(album):
            return False
        return True

    def db_add_review(user_id, album_id, title, content, star_rating, submission_date):
        """
        Used to add a new review for an album in the database. Additionally, connects review to user and album
        Params:
        - user_id: ID of user who added the review
        - album_id: ID of the target album
        - title: Title of the review
        - content: Textual contents of the review
        - star_rating: Rating from 1-5
        - submission_date: Date when the review was submitted dd-mm-YYYY
        Returns: True if successful; False otherwise
        """
        print("Adding new review for album {}".format(album_id))
        # If a date is provided, make sure its proper
        submission_date = to_date(submission_date)
        if submission_date is None:
            return False
        # Create the review entity
        review = Review(
            title=title,
            content=content,
            star_rating=star_rating,
            submission_date=submission_date
        )
        # Connect review to user and album
        user = User.query.filter_by(id=user_id).first()
        album = Album.query.filter_by(id=album_id).first()
        if user is None or album is None:
            print("Adding review failed. User and/or album doesn't exist")
            return False
    
        review.user = user
        review.album = album
        user.reviews.append(review)
        album.reviews.append(review)
        
        # Stage changes
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        # Commit changes
        try:
            db.session.commit()
        except IntegrityError:
            print("Failed to add review!")
            return False
        return True
        

    def db_add_tag(user_id, review_id, meaning="useful"):
        """
        Used to tag a review useful/not useful in the database. Additionally, connects tag to user and review
        Params:
        - user_id: ID of the user tagging a review
        - review_id: ID of target review
        - meaning: Either "useful" or "not useful"
        Returns: True if successful; False otherwise
        """
        # Make sure meaning is on of the available ones
        if meaning not in ["useful", "not useful"]:
            print("Incorrect tag meaning. Use \"useful\" or \"not useful\"")
            return False
        print("Adding \"{}\" tag to review {}".format(meaning, review_id))
        # Create the new tag entity
        tag = Tag(
            meaning=meaning
        )
        # Connect tag to user and review
        user = User.query.filter_by(id=user_id).first()
        review = Review.query.filter_by(id=review_id).first()
        if user is None or review is None:
            print("Adding tag failed. User and/or review doesn't exist")
            return False
        tag.user = user
        tag.review = review
        user.tags.append(tag)
        review.tags.append(tag)
        # Stage changes
        db.session.add(tag)
        db.session.add(user)
        db.session.add(review)
        # Commit changes
        try:
            db.session.commit()
        except IntegrityError:
            print("Failed to add tag!")
            return False
        return True

    def commit_to_db(entity):
        """
        Performs the the actual database commit.
        Params:
        - entitty: Entitity to add. Based on one of the models
        Returns: True if successful; False otherwise
        """
        db.session.add(entity)
        try:
            db.session.commit()
            return True
        except IntegrityError:
            print("Failed to add entity to db, rolling back!")
            db.session.rollback()
            return False
