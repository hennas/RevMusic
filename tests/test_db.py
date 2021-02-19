import os
import pytest
import tempfile
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, StatementError

from revmusic.utils import to_date
from revmusic import create_app, db
from revmusic.models import User, Album, Review, Tag

# RUN WITH: $ python3 -m pytest tests

@pytest.fixture
def app():
    """
    Setup the revmusic database for testing
    @pytest.fixture decoration ensures that all functions starting with test_ are ran
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
    yield app
    # Close the temp files
    os.close(db_fd)
    os.unlink(db_fname)

#######################
# Boilerplate functions
#######################

def _get_user(username, email, password):
    """
    Generate a user
    """
    return User(
        username=username,
        email=email,
        password=password
    )

def _get_album(title, artist, publication_date=None, duration=None, genre=None):
    """
    Generate an album
    """
    return Album(
        title=title,
        artist=artist,
        publication_date=to_date(publication_date),
        duration=duration,
        genre=genre
    )

def _get_review(title, content, star_rating, submission_date):
    """
    Generate a review
    """
    return Review(
        title=title,
        content=content,
        star_rating=star_rating,
        submission_date=to_date(submission_date)
    )

def _get_tag(meaning="useful"):
    """
    Generate a tag
    """
    return Tag(
        meaning=meaning
    )

#######
# TESTS
#######

def test_create_instances(app):
    """
    Tests that we can create one of each model and add them to the DB
    using valid values. Also checks that relationships are saved correctly
    """
    with app.app_context():
        # Create the instances
        user = _get_user('test_user', 'test@gmail.com', 'a'*64)
        album = _get_album('test album', 'test artist', '10-10-2020', 120, 'test metal')
        review = _get_review('test review', 'test review text', 5, '10-10-2020')
        tag = _get_tag('useful')
        # Connect review to user & album
        user.reviews.append(review)
        album.reviews.append(review)
        review.user = user
        review.album = album
        # Connect tag to user & review
        user.tags.append(tag)
        review.tags.append(tag)
        tag.user = user
        tag.review = review
        # Stage changes
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        db.session.add(tag)
        # Commit changes
        db.session.commit()

        # Check that everything was added correctly to the db
        assert User.query.count() == 1
        assert Album.query.count() == 1
        assert Review.query.count() == 1
        assert Tag.query.count() == 1
        db_user = User.query.first()
        db_album = Album.query.first()
        db_review = Review.query.first()
        db_tag = Tag.query.first()

        # Check relations
        assert db_review in db_user.reviews
        assert db_review in db_album.reviews
        assert db_review.user == db_user
        assert db_review.album == db_album
        assert db_tag in db_user.tags
        assert db_tag in db_review.tags
        assert db_tag.user == db_user
        assert db_tag.review == db_review
    
def test_tag_one_to_one(app):
    """
    Test that a tag can't be assigned to multiple reviews/users
    """
    with app.app_context:
        user1 = _get_user('test_user', 'test@gmail.com', 'a'*64)
        user2 = _get_user('test_user2', 'test2@gmail.com', 'a'*64)
        