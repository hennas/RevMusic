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
    if publication_date == "test":
        pass
    elif publication_date is not None:
        publication_date = to_date(publication_date)

    return Album(
        title=title,
        artist=artist,
        publication_date=publication_date,
        duration=duration,
        genre=genre
    )

def _get_review(title, content, star_rating, submission_date):
    """
    Generate a review
    """
    if submission_date == "test":
        pass
    elif submission_date is not None:
        submission_date = to_date(submission_date)

    return Review(
        title=title,
        content=content,
        star_rating=star_rating,
        submission_date=submission_date
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

def test_user_column(app):
    """
    Tests the constraints of the User column
    """
    with app.app_context():
        # Check that username can't be null
        user = _get_user(None, 'None', 'a'*64)
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that email can't be null
        user = _get_user('None', None, 'a'*64)
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that password can't be null
        user = _get_user('None', 'None', None)
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_user_uniqueness(app):
    """
    Test that users are always unique, as they should be
    """
    with app.app_context():
        # Test based on username
        user1 = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('a', 'b', 'a'*64)
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test based on email
        user1 = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('b', 'a', 'a'*64)
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test based on username&email
        user1 = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('a', 'a', 'a'*64)
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that two diffent ones can be added
        user1 = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('b', 'b', 'a'*64)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        assert User.query.count() == 2

def test_user_info_update(app):
    """
    Tests that user model's values can be updated
    """
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        db.session.add(user)
        db.session.commit()
        
        # Update All values
        user = User.query.first()
        user.username = 'b'
        user.email = 'c'
        user.password = 'd'*64
        db.session.add(user)
        db.session.commit()
        
        user = User.query.first()
        assert user.username == 'b'
        assert user.email == 'c'
        assert user.password == 'd'*64

def test_user_delete(app):
    """
    Test that a user can be deleted
    """
    with app.app_context():
        user = _get_user('a', 'a', 'b'*64)
        db.session.add(user)
        db.session.commit()
        user = User.query.first()
        db.session.delete(user)
        db.session.commit()
        assert User.query.count() == 0


def test_album_column(app):
    """
    Tests the constraints of the Album column
    """
    with app.app_context():
        # Check that publication_date, duration and genre can be Null
        album1 = _get_album('a', 'a')
        db.session.add(album1)
        db.session.commit()
        assert Album.query.count() == 1

        # Check that title can't be null
        album2 = _get_album(None, 'a')
        db.session.add(album2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that artist can't be null
        album2 = _get_album('a', None)
        db.session.add(album2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that publication_date only accepts dates
        album2 = _get_album('a', 'a', 'test')
        db.session.add(album2)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # Check that duration only accepts integers
        album2 = _get_album('a', 'a', duration='a')
        db.session.add(album2)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # Checks that numbers can't be too big
        album2 = _get_album('a', 'a', duration=9999*9999^123)
        db.session.add(album2)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

def test_album_uniqueness(app):
    """
    Tests the uniquety constraint of the album model
    """
    with app.app_context():
        album1 = _get_album('a', 'a')
        album2 = _get_album('a', 'a')
        album3 = _get_album('a', 'b')
        album4 = _get_album('b', 'a')

        # Same title and artist
        db.session.add(album1)
        db.session.add(album2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        # Same title, different artist
        db.session.add(album1)
        db.session.add(album3)
        db.session.commit()
        assert Album.query.count() == 2
        # Different title, same artist
        db.session.add(album4)
        db.session.commit()
        assert Album.query.count() == 3

def test_album_info_update(app):
    """
    Tests that album model's values can be updated
    """
    with app.app_context():
        album = _get_album('a', 'a', '10-10-2020', 100, 'a')
        db.session.add(album)
        db.session.commit()
        
        # Update All values
        album = Album.query.first()
        album.title = 'b'
        album.artist = 'c'
        album.publication_date = to_date('20-10-2021')
        album.duration = 10
        album.genre = 'd'
        db.session.add(album)
        db.session.commit()
        
        album = Album.query.first()
        assert album.title == 'b'
        assert album.artist == 'c'
        assert album.publication_date == to_date('20-10-2021')
        assert album.duration == 10
        assert album.genre == 'd'

def test_album_delete(app):
    """
    Test that a album can be deleted
    """
    with app.app_context():
        album = _get_album('a', 'a')
        db.session.add(album)
        db.session.commit()
        album = Album.query.first()
        db.session.delete(album)
        db.session.commit()
        assert Album.query.count() == 0

def test_review_column(app):
    """
    Tests the review column's constraints
    """
    with app.app_context():
        # Test that title can't be null
        review = _get_review(None, 'a', 5, '01-01-2020')
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that content can't be null
        review = _get_review('a', None, 5, '01-01-2020')
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that star_rating can't be null
        review = _get_review('a', 'a', None, '01-01-2020')
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that date can't be null
        review = _get_review('a', 'a', 5, None)
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that star_rating must be integer
        review = _get_review('a', 'a', 'a', '01-01-2020')
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # Test that star_rating can't be too big number
        review = _get_review('a', 'a', 9999*9999^123, '01-01-2020')
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

def test_review_uniqueness(app):
    """
    Test the review model's uniqueness constraint
    """
    with app.app_context():
        user1 = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('b', 'b', 'a'*64)
        album1 = _get_album('a', 'a')
        album2 = _get_album('b', 'b')
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(album1)
        db.session.add(album2)
        db.session.commit()

        review1 = _get_review('a', 'a', 5, '01-01-2020')
        review2 = _get_review('a', 'a', 5, '01-01-2020')
        # Same user and album id
        review1.user_id = 1
        review1.album_id = 1
        review2.user_id = 1
        review2.album_id = 1
        db.session.add(review1)
        db.session.add(review2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        
        # Different ids
        review2.user_id = 2
        review2.album_id = 2
        db.session.add(review1)
        db.session.add(review2)
        db.session.commit()
        assert Review.query.count() == 2

def test_review_info_update(app):
    """
    Tests that album model's values can be updated
    """
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 1, '10-10-2020')
        review.user = user
        review.album = album
        db.session.add(review)
        db.session.commit()
        
        # Update All values
        review = Review.query.first()
        review.title = 'b'
        review.content = 'c'
        review.star_rating = 5
        review.submission_date = to_date('20-10-2021')
        db.session.add(review)
        db.session.commit()
        
        review = Review.query.first()
        assert review.title == 'b'
        assert review.content == 'c'
        assert review.star_rating == 5
        assert review.submission_date == to_date('20-10-2021')

def test_review_delete(app):
    """
    Tests that a review can be deleted
    """
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 1, '10-10-2020')
        review.user = user
        review.album = album
        db.session.add(review)
        db.session.commit()
        review = Review.query.first()
        db.session.delete(review)
        db.session.commit()
        assert Review.query.count() == 0

def test_tag_column(app):
    """
    Test the tag column's constraints
    """
    with app.app_context():
        # Make sure the meaning can't be too long
        tag = _get_tag('a'*100)
        db.session.add(tag)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_tag_info_update(app):
    """
    Tests that album model's values can be updated
    """
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 1, '10-10-2020')
        review.user = user
        review.album = album
        tag = _get_tag()
        tag.user = user
        tag.review = review
        db.session.add(tag)
        db.session.commit()
        
        # Update All values
        tag = Tag.query.first()
        tag.meaning = 'not useful'
        db.session.add(tag)
        db.session.commit()
        
        tag = Tag.query.first()
        assert tag.meaning == 'not useful'

def test_tag_delete(app):
    """
    Tests that a tag can be deleted
    """
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 1, '10-10-2020')
        tag = _get_tag()
        review.user = user
        review.album = album
        tag.user = user
        tag.review = review
        db.session.add(tag)
        db.session.commit()
        tag = Tag.query.first()
        db.session.delete(tag)
        db.session.commit()
        assert Tag.query.count() == 0