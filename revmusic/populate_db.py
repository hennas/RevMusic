import click
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError

from . import db
from .models import User, Album, Review, Tag
from .utils import to_date

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Force foreing key
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Useful link for viewing .db file contents: https://inloop.github.io/sqlite-viewer/

####################
# Addition functions
####################

def add_user(username, email, password):
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
    if not commit_to_db(user):
        return False
    return True

def add_album(title, artist, publication_date=None, duration=None, genre=None):
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
    if not commit_to_db(album):
        return False
    return True

def add_review(user_id, album_id, title, content, star_rating, submission_date):
    """
    Used to add a new review for an album in the database
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
        user_id=user_id,
        album_id=album_id,
        title=title,
        content=content,
        star_rating=star_rating,
        submission_date=submission_date
    )
    # Attempt to add
    if not commit_to_db(review):
        return False
    return True

def add_tag(user_id, review_id, meaning="useful"):
    """
    Used to tag a review useful/not useful in the database
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
        user_id=user_id,
        review_id=review_id,
        meaning=meaning
    )
    # Attempt to add
    if not commit_to_db(tag):
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

@click.command(name="populate-db", help="Populates the database with hardcoded data")
@with_appcontext
def populate_db_cmd():
    """
    Populates the database with example values
    """
    print("Populating the database...")
    try:
        add_user('admin', 'root@admin.com', '9750c9fbe856aa813c24f08b0faeba79f4f9b0d05102d4833fac8a6a5f694827')
        add_user('YTC', 'rapper@g_mail.com', '35f27d1ae747e233e966c9502427098c9d713c415a95fe47a0a855c5fecd243e')
        add_album('Iäti Vihassa ja Kunniassa', 'Vitsaus', '05-12-2004', '120', 'black metal')
        add_album('Kun Synkkä Ikuisuus Avautuu', 'Horna', genre='black metal')
        add_review(1, 1, 'Finally soome good black metal!', 'I really like this album :)', 5, '19-02-2021')
        add_review(2, 2, "I don't like black metal", 'Why am I even here?', 1, '19-02-2021')
        add_tag(1, 1, 'useful')
        add_tag(1, 2, 'not useful')
    except OperationalError:
        print('SQL Operational Error happend! Has the db been initialized?')
        return
    print("Done populating!")
