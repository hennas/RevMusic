import click
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError

from . import db
from .models import User, Album, Review, Tag
from .utils import to_date, to_time, to_datetime


# Useful link for viewing .db file contents: https://inloop.github.io/sqlite-viewer/
@click.command(name="populate-db", help="Populates the database with hardcoded data")
@with_appcontext
def populate_db_cmd():
    """
    Populates the database with example values
    """
    print("Populating the database...")
    user1 = User(username='admin', email='root@admin.com', password='9e81d8ab3b3bc5853467dc1fd8a8afcbde52ed71b7c170d8802a86ffa9e226a8')
    user2 = User(username='ytc fan', email='best_rapper@gmail.com', password='b4fdf2ea4fd3222ea3ca97ebf3835de15c7a27b704eca26317a8cf2dba925bc1')
    # Create 3 albums
    album1 = Album(unique_name='iäti vihassa ja kunniassa', title='Iäti Vihassa ja Kunniassa', artist='Vitsaus', publication_date=to_date('2004-12-12'), duration=to_time('01:08:06'), genre='Black Metal')
    album2 = Album(unique_name='stc is the greatest', title='STC is the Greatest', artist='Spamtec', publication_date=to_date('2004-01-01'), duration=to_time('01:01:00'), genre='Nerdcore')
    album3 = Album(unique_name='rota', title='Rota', artist='Wyrd')
    # Create 2 reviews
    review1 = Review(identifier='review_27032021133658', title='Finally some good black metal!', content='This is so good! Much better than posers like Wolves in the Throne Room', star_rating=5, submission_date=to_datetime('2021-03-25 13:36:56'))
    review2 = Review(identifier='review_250320211334445', title='STC STILL THE GREATES!', content='I still listen to YTC and Phlow after all these years because this album is so good', star_rating=5, submission_date=to_datetime('2021-03-27 13:44:45'))
    # Create 2 tags
    tag1 = Tag(identifier='tag_25032021134913', meaning='usefull', date_created=to_datetime('2021-03-25 13:49:13'))
    tag2 = Tag(identifier='tag_27032021135025', meaning='not usefull', date_created=to_datetime('2021-03-27 13:50:25'))
    # Set review relations
    review1.user = user1
    review1.album = album1
    review2.user = user2
    review2.album = album2
    # Set tag relations
    tag1.user = user2
    tag1.review = review1
    tag2.user = user1
    tag2.review = review2
    # Add to DataBase
    try:
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(album1)
        db.session.add(album2)
        db.session.add(review1)
        db.session.add(review2)
        db.session.add(tag1)
        db.session.add(tag2)
        db.session.commit()
        print("Done populating!")
    except:
        print("Populating the database failed. Is the database initialized and empty? Try running db-init and retry after that.")
