import os
import pytest
import tempfile
import datetime
from sqlalchemy import event, func
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, StatementError

from revmusic import create_app, db
from revmusic.utils import to_date, to_time, to_datetime
from revmusic.models import User, Album, Review, Tag


# RUN WITH: $ python3 -m pytest -s tests
# The example python project provided by the course assistants was a basis for this
@pytest.fixture
def app():
    """
    Setup the revmusic database for testing
    @pytest.fixture decoration ensures that all functions starting with test_ are run
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

def _get_user(username='a', email='a@a.com', password='a'*64):
    """
    Generate a user
    """
    return User(
        username=username,
        email=email,
        password=password
    )

def _get_album(title='a', unique_name='a', artist='a', publication_date='2021-01-01', duration='01:01:01', genre=None):
    """
    Generate an album
    """
    return Album(
        title=title,
        unique_name=unique_name,
        artist=artist,
        publication_date=to_date(publication_date),
        duration=to_time(duration),
        genre=genre
    )

def _get_review(title='a', identifier='a', content='a', star_rating=5, submission_date='2021-01-01 10:10:10'):
    """
    Generate a review
    """
    return Review(
        title=title,
        identifier=identifier,
        content=content,
        star_rating=star_rating,
        submission_date=to_datetime(submission_date)
    )

def _get_tag(identifier='a', meaning='useful', date_created='2021-01-01 10:10:10'):
    """
    Generate a tag
    """
    return Tag(
        identifier=identifier,
        meaning=meaning,
        date_created=to_datetime(date_created)
    )

#######
# TESTS
#######

def test_create_instances(app):
    """
    Tests that we can create an instance of each model and add them to the DB
    using valid values. Also checks that relationships are saved correctly
    """
    print('\n\n================RUNNING DATABASE TESTS================')
    print('Testing basic instance and relation creation: ', end='')
    with app.app_context():
        # Create the instances
        user = _get_user()
        album = _get_album()
        review = _get_review()
        tag = _get_tag()
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
    Tests the attribute constraints of the User model
    """
    print('\nTesting the user column: ', end='')
    with app.app_context():
        # Check that username can't be null
        user = _get_user(username=None)
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that email can't be null
        user = _get_user(email=None)
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that password can't be null
        user = _get_user(password=None)
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check foreign key violations
        user = _get_user()
        violation = _get_album()
        # Reviews
        with pytest.raises(KeyError):
            user.reviews.append(violation)
        # Tags
        with pytest.raises(KeyError):
            user.tags.append(violation)

def test_user_uniqueness(app):
    """
    Test that users are always unique, as they should be
    """
    print('\nTesting user uniqueness: ', end='')
    with app.app_context():
        # Test based on username
        user1 = _get_user(email='a')
        user2 = _get_user(email='b')
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test based on email
        user1 = _get_user(username='a')
        user2 = _get_user(username='b')
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test based on username&email
        user1 = _get_user()
        user2 = _get_user()
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that two different ones can be added
        user1 = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('b', 'b', 'a'*64)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        assert User.query.count() == 2

def test_user_retrieve(app):
    """
    Test retrieving existing users with different filters
    """
    print('\nTesting user retrieving: ', end='')
    with app.app_context():
        user1 = _get_user('test user', 'tester@gmail.com', 'a'*64)
        user2 = _get_user('tester', 'test_user@gmail.com', 'b'*64)
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        # Filter based on username
        assert User.query.filter_by(username='test user').count() == 1
        assert User.query.filter_by(username='tester').count() == 1
        assert User.query.filter_by(username='t=======esterr').count() == 0
        # Filter based on email
        assert User.query.filter_by(email='tester@gmail.com').count() == 1
        assert User.query.filter_by(email='test_user@gmail.com').count() == 1
        assert User.query.filter_by(email='gmail.com').count() == 0
        assert User.query.filter_by(email='test user@gmail.com').count() == 0


def test_user_info_update(app):
    """
    Tests that User model's values can be updated
    """
    print('\nTesting user info updating: ', end='')
    with app.app_context():
        user = _get_user()
        db.session.add(user)
        db.session.commit()
        
        # Update all values
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
    print('\nTesting user deletion: ', end='')
    with app.app_context():
        user = _get_user()
        db.session.add(user)
        db.session.commit()
        user = User.query.first()
        db.session.delete(user)
        db.session.commit()
        assert User.query.count() == 0


def test_album_column(app):
    """
    Tests the attribute constraints of the Album model
    """
    print('\nTesting the album column: ', end='')
    with app.app_context():
        # Check that publication_date, duration and genre can be Null
        album1 = _get_album(publication_date=None, duration=None, genre=None)
        db.session.add(album1)
        db.session.commit()
        assert Album.query.count() == 1

        # Check that unique_name can't be null
        album2 = _get_album(unique_name=None)
        db.session.add(album2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that title can't be null
        album2 = _get_album(title=None)
        db.session.add(album2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that artist can't be null
        album2 = _get_album(artist=None)
        db.session.add(album2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Check that publication_date only accepts dates
        album2 = _get_album()
        album2.publication_date = '2021-01-01'
        db.session.add(album2)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # Check that duration only accepts times
        album2 = _get_album(duration='a')
        db.session.add(album2)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # Check foreign key violations
        album = _get_album()
        violation = _get_user()
        # Reviews
        with pytest.raises(KeyError):
            album.reviews.append(violation)

def test_album_uniqueness(app):
    """
    Tests the uniqueness constraint of the Album model
    """
    print('\nTesting album uniqueness: ', end='')
    with app.app_context():
        album1 = _get_album()
        album2 = _get_album()
        album3 = _get_album(artist='b', unique_name='b')
        album4 = _get_album(title='b', unique_name='c')
        album5 = _get_album(title='c', unique_name='c')

        # Same title and artist; uniqueness constraint requires that there cannot be two rows with the same album title and artist
        db.session.add(album1)
        db.session.add(album2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        # Same title, different artist can be added
        db.session.add(album1)
        db.session.add(album3)
        db.session.commit()
        assert Album.query.count() == 2
        # Different title, same artist can be added
        db.session.add(album4)
        db.session.commit()
        assert Album.query.count() == 3
        # Same unique_name should fail
        db.session.add(album4)
        db.session.add(album5)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_album_retrieve(app):
    """
    Test retrieving existing albums with different filters
    """
    print('\nTesting album retrieving: ', end='')
    with app.app_context():
        album1 = _get_album('Victory or Valhalla', 'victory or valhalla', 'Vuohikuu', '2020-10-10', '10:10:10', 'black metal')
        album2 = _get_album('Polla Stelaris', 'polla stelaris', 'Vuohikuu', '2001-10-10', '10:10:10', 'black metal')
        album3 = _get_album('Serious Business', 'serious business', 'YTC', '2020-10-10', '00:10:00', 'rap')
        album4 = _get_album('You Suffer', 'you suffer', 'Napalm Death', '2022-10-10', '00:00:03', 'trash')
        db.session.add(album1)
        db.session.add(album2)
        db.session.add(album3)
        db.session.add(album4)
        # Filter based on title
        assert Album.query.filter_by(title='Serious Business').count() == 1
        assert Album.query.filter_by(title='YouSuffer').count() == 0
        # Filter based on artist
        assert Album.query.filter_by(artist='Vuohikuu').count() == 2
        assert Album.query.filter_by(artist='YTc').count() == 0
        # Filter based on unique_name
        assert Album.query.filter_by(unique_name='victory or valhalla').count() == 1
        assert Album.query.filter_by(unique_name='victory or halpahalli').count() == 0
        # Filter based on publication_date
        assert Album.query.filter_by(publication_date=to_date('2020-10-10')).count() == 2
        assert Album.query.filter_by(publication_date=to_date('2001-10-10')).count() == 1
        assert Album.query.filter_by(publication_date=to_date('2021-10-10')).count() == 0
        # Filter based on duration
        assert Album.query.filter_by(duration=to_time('10:10:10')).count() == 2
        assert Album.query.filter_by(duration=to_time('00:00:03')).count() == 1
        assert Album.query.filter_by(duration=to_time('11:11:11')).count() == 0
        # Filter based on genre
        assert Album.query.filter_by(genre='black metal').count() == 2
        assert Album.query.filter_by(genre='trash').count() == 1
        assert Album.query.filter_by(genre='thrash').count() == 0

def test_album_info_update(app):
    """
    Tests that Album model's values can be updated
    """
    print('\nTesting album info updating: ', end='')
    with app.app_context():
        album = _get_album()
        db.session.add(album)
        db.session.commit()
        
        # Update all values
        album = Album.query.first()
        album.title = 'b'
        album.artist = 'c'
        album.publication_date = to_date('20-10-2021')
        album.duration = to_time('00:00:03')
        album.genre = 'd'
        db.session.add(album)
        db.session.commit()
        
        album = Album.query.first()
        assert album.title == 'b'
        assert album.artist == 'c'
        assert album.publication_date == to_date('20-10-2021')
        assert album.duration == to_time('00:00:03')
        assert album.genre == 'd'

def test_album_delete(app):
    """
    Test that a album can be deleted
    """
    print('\nTesting album deletion: ', end='')
    with app.app_context():
        album = _get_album()
        db.session.add(album)
        db.session.commit()
        album = Album.query.first()
        db.session.delete(album)
        db.session.commit()
        assert Album.query.count() == 0

def test_review_column(app):
    """
    Tests the attribute constraints for Review model
    """
    print('\nTesting review column: ', end='')
    with app.app_context():
        # Test that identifier can't be null
        review = _get_review(identifier=None)
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


        # Test that title can't be null
        review = _get_review(title=None)
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that content can't be null
        review = _get_review(content=None)
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that star_rating can't be null
        review = _get_review(star_rating=None)
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that date can't be null
        review = _get_review(submission_date=None)
        db.session.add(review)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Test that star_rating must be integer
        review = _get_review(star_rating='a')
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # Test that star_rating can't be too big number
        review = _get_review(star_rating=9999*9999^123)
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # Check foreign key violations
        review = _get_review()
        violation1 = _get_user()
        violation2 = _get_album()
        # FK to user cannot reference anything else but an instance of User model
        with pytest.raises(ValueError):
            review.user = violation2
        # FK to album cannot reference anything else but an instance of Album model
        with pytest.raises(ValueError):
            review.album = violation1
        # Check that Null foreign keys not allowed
        review = _get_review(title="I don't like foreign keys")
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

        # FK pointing to non-existent entity (not allowed)
        review = _get_review()
        review.user_id = 100
        review.album_id = 200
        db.session.add(review)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

def test_review_uniqueness(app):
    """
    Test the Review model's uniqueness constraint
    """
    print('\nTesting review uniqueness: ', end='')
    with app.app_context():
        user1 = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('b', 'b', 'a'*64)
        album1 = _get_album('a', 'a', 'a')
        album2 = _get_album('b', 'b', 'b')
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(album1)
        db.session.add(album2)
        db.session.commit()

        review1 = _get_review('a', 'c', 'a')
        review2 = _get_review('a', 'd', 'a')
        # Same user and album id; there cannot be two reviews made by the same user to the same album
        review1.user_id = 1
        review1.album_id = 1
        review2.user_id = 1
        review2.album_id = 1
        db.session.add(review1)
        db.session.add(review2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        
        # Different ids allowed
        review2.user_id = 2
        review2.album_id = 2
        db.session.add(review1)
        db.session.add(review2)
        db.session.commit()
        assert Review.query.count() == 2

def test_review_retrieve(app):
    """
    Test retrieving existing reviews with different filters
    """
    print('\nTesting review retrieving: ', end='')
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('b', 'b', 'b'*64)
        album = _get_album('a', 'a')
        album2 = _get_album('b', 'b')
        album3 = _get_album('c', 'c')

        review1 = _get_review('a', 'a', 'a is a good album', 5)
        review1.user = user
        review1.album = album

        review2 = _get_review('b', 'b', 'b is a bad album', 1, '2022-02-01 00:00:00')
        review2.user = user
        review2.album = album2

        db.session.add(review1)
        db.session.add(review2)
        db.session.add(user2)
        db.session.add(album3)
        db.session.commit()

        # Filter by identifier
        assert Review.query.filter_by(identifier='a').count() == 1
        assert Review.query.filter_by(identifier='d').count() == 0
        # Filter by user
        assert Review.query.filter_by(user=user).count() == 2
        assert Review.query.filter_by(user=user2).count() == 0
        # Filter by album
        assert Review.query.filter_by(album=album).count() == 1
        assert Review.query.filter_by(album=album2).count() == 1
        assert Review.query.filter_by(album=album3).count() == 0
        # Filter by title
        assert Review.query.filter_by(title='a').count() == 1
        assert Review.query.filter_by(title='c').count() == 0
        # Filter by content
        assert Review.query.filter_by(content='a is a good album').count() == 1
        assert Review.query.filter_by(content='a is agood album').count() == 0
        # Filter by submission_date
        assert Review.query.filter(func.date(Review.submission_date) >= '2018-01-01').filter(func.date(Review.submission_date) <= '2022-02-01').count() == 2
        assert Review.query.filter(func.date(Review.submission_date) >= '2018-01-01').filter(func.date(Review.submission_date) <= '2022-01-01').count() == 1
        # Filter by star_rating
        assert Review.query.filter_by(star_rating=5).count() == 1
        assert Review.query.filter_by(star_rating=1).count() == 1
        assert Review.query.filter_by(star_rating=4).count() == 0

def test_review_info_update(app):
    """
    Tests that Album model's values can be updated
    """
    print('\nTesting review info updating: ', end='')
    with app.app_context():
        user = _get_user()
        album = _get_album()
        review = _get_review()
        review.user = user
        review.album = album
        db.session.add(review)
        db.session.commit()
        
        # Update all values
        review = Review.query.first()
        review.title = 'b'
        review.content = 'c'
        review.star_rating = 1
        review.submission_date = to_datetime('2021-10-10 13:13:13')
        db.session.add(review)
        db.session.commit()
        
        review = Review.query.first()
        assert review.title == 'b'
        assert review.content == 'c'
        assert review.star_rating == 1
        assert review.submission_date == to_datetime('2021-10-10 13:13:13')

def test_review_delete(app):
    """
    Tests that a review can be deleted
    """
    print('\nTesting review deletion: ', end='')
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
    Test the attribute constraints of Tag model
    """
    print('\nTesting the tag column: ', end='')
    with app.app_context():
        # Check foreign key violations
        tag = _get_tag()
        violation1 = _get_user('a', 'a', 'a'*64)
        violation2 = _get_review('a', 'a', 5, '10-10-2020')
        # FK to user cannot reference anything else but an instance of User model
        with pytest.raises(ValueError):
            tag.user = violation2
        # FK to review cannot reference anything else but an instance of Review model
        with pytest.raises(ValueError):
            tag.review = violation1
        # Check that Null foreign keys are not allowed
        db.session.add(tag)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()
        # FK pointing to non-existent entity (not allowed) deleting a 
        db.session.add(tag)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()
        # date_created can't be null
        tag = _get_tag(date_created=None)
        db.session.add(tag)
        with pytest.raises(StatementError):
            db.session.commit()
        db.session.rollback()

def test_tag_uniqueness(app):
    """
    Tests the uniqueness constraint of the Tag model
    """
    print('\nTesting tag uniqueness: ', end='')
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 1, '10-10-2020')
        review.user = user
        review.album = album
        tag = _get_tag()
        tag.user = user
        tag.review = review
        tag2 = _get_tag(identifier='b', meaning='not useful')
        tag2.user = user
        tag2.review = review

        # Same user and review; uniqueness constraint requires that the same user cannot tag the same review twice
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        db.session.add(tag)
        db.session.add(tag2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        # Identifier must be unqieu
        tag2 = _get_tag()
        db.session.add(tag)
        db.session.add(tag2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        
def test_tag_retrieve(app):
    """
    Test retrieving existing tags with different filters
    """
    print('\nTesting tag retrieving: ', end='')
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        user2 = _get_user('b', 'b', 'b'*64)
        album = _get_album('a', 'a')
        album2 = _get_album('b', 'b')
        review = _get_review('a', 'a', 'a', 1)
        review2 = _get_review('b', 'b', 'b', 1)
        review.user = user
        review.album = album
        review2.user = user2
        review2.album = album2
        tag = _get_tag()
        tag.user = user
        tag.review = review
        tag2 = _get_tag(identifier='b', meaning='not useful')
        tag2.user = user
        tag2.review = review2
        db.session.add(user)
        db.session.add(user2)
        db.session.add(album)
        db.session.add(user2)
        db.session.add(review)
        db.session.add(review2)
        db.session.add(tag)
        db.session.add(tag2)
        db.session.commit()

        # Filter by identifier
        assert Tag.query.filter_by(identifier='a').count() == 1
        assert Tag.query.filter_by(identifier='c').count() == 0
        # Filter by user
        assert Tag.query.filter_by(user=user).count() == 2
        assert Tag.query.filter_by(user=user2).count() == 0
        # Filter by review
        assert Tag.query.filter_by(review=review).count() == 1
        assert Tag.query.filter_by(review=review2).count() == 1
        # Filter by meaning
        assert Tag.query.filter_by(meaning="useful").count() == 1
        assert Tag.query.filter_by(meaning="not useful").count() == 1
        assert Tag.query.filter_by(meaning="usefull").count() == 0

def test_tag_info_update(app):
    """
    Tests that Tag model's values can be updated
    """
    print('\nTesting tag info updating: ', end='')
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 'a', 1)
        review.user = user
        review.album = album
        tag = _get_tag()
        tag.user = user
        tag.review = review
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        db.session.add(tag)
        db.session.commit()
        
        # Update all values
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
    print('\nTesting tag delition: ', end='')
    with app.app_context():
        user = _get_user('a', 'a', 'a'*64)
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 'a', 1)
        tag = _get_tag()
        review.user = user
        review.album = album
        tag.user = user
        tag.review = review
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        db.session.add(tag)
        db.session.commit()
        tag = Tag.query.first()
        db.session.delete(tag)
        db.session.commit()
        assert Tag.query.count() == 0

def test_ondelete(app):
    """
    Tests that onDelete works as expected
    """
    print('\nTesting onDeletes: ', end='')
    with app.app_context():
        user = _get_user()
        album = _get_album()
        review = _get_review()
        review.user = user
        review.album = album
        tag = _get_tag()
        tag.user = user
        tag.review = review
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        db.session.add(tag)
        db.session.commit()

        # Test that tag is removed from user and review once its deleted
        tag = Tag.query.first()
        db.session.delete(tag)
        db.session.commit()
        review = Review.query.first()
        user = User.query.first()
        assert len(user.tags) == 0
        assert (len(review.tags)) == 0

        # Test that tag and review are removed from user and album once review is removed
        tag = _get_tag()
        tag.user = user
        tag.review = review
        db.session.add(tag)
        db.session.commit()
        review = Review.query.first()
        db.session.delete(review)
        db.session.commit()
        user = User.query.first()
        album = Album.query.first()
        assert len(user.reviews) == 0
        assert len(album.reviews) == 0
        assert Tag.query.count() == 0

        # Test that review and tag are deleted when album is deleted
        review = _get_review('a', 'a', 5, '10-10-2020')
        review.user = user
        review.album = album
        tag = _get_tag()
        tag.user = user
        tag.review = review
        db.session.add(review)
        db.session.add(tag)
        db.session.commit()
        album = Album.query.first()
        db.session.delete(album)
        db.session.commit()
        assert Review.query.count() == 0
        assert Tag.query.count() == 0

        # Test that review and tag are deleted when user is deleted
        user = User.query.first()
        album = _get_album('a', 'a')
        review = _get_review('a', 'a', 5, '10-10-2020')
        review.user = user
        review.album = album
        tag = _get_tag()
        tag.user = user
        tag.review = review
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        db.session.add(tag)
        db.session.commit()
        user = User.query.first()
        db.session.delete(user)
        db.session.commit()
        assert Review.query.count() == 0
        assert Tag.query.count() == 0

def test_onupdate(app):
    """
    Tests that onUpdate works as expected
    (Testing onUpdate is quite trivial in this case, as FKs point to the primary keys, which should not ever change)
    """
    print('\nTesting onUpdates: ', end='')
    with app.app_context():
        user = _get_user()
        album = _get_album()
        review = _get_review()
        review.user = user
        review.album = album
        tag = _get_tag()
        tag.user = user
        tag.review = review
        db.session.add(user)
        db.session.add(album)
        db.session.add(review)
        db.session.add(tag)
        db.session.commit()

        # Test that updating user and album id updates user and album FKs in review and tag
        user = User.query.first()
        album = Album.query.first()
        user.id = 10
        album.id = 16
        db.session.add(user)
        db.session.add(album)
        db.session.commit()
        assert Review.query.first().user.id == 10
        assert Review.query.first().album.id == 16
        assert Tag.query.first().user.id == 10

        # Test that updating review and tag id updates user, album, review and tag
        review = Review.query.first()
        tag = Tag.query.first()
        review.id = 13
        tag.id = 36
        db.session.add(review)
        db.session.add(tag)
        db.session.commit()
        assert User.query.first().reviews[0].id == 13
        assert User.query.first().tags[0].id == 36
        assert Album.query.first().reviews[0].id == 13
        assert Review.query.first().tags[0].id == 36
        assert Tag.query.first().review.id == 13
