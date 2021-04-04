import os
import click
from flask import Flask
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError

# The database is required here. Defined in __init__.py
from revmusic import db


class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    
    reviews = db.relationship("Review", cascade="all, delete-orphan", back_populates="user")
    tags = db.relationship("Tag", cascade="all, delete-orphan", back_populates="user")
    
    def __repr__(self):
        return "{} <{}>".format(self.username, self.id)

    @staticmethod
    def get_schema():
        schema = {
            'type': 'object',
            'required': ['username', 'email', 'password']
        }
        props = schema['properties'] = {}
        props['username'] = {
            'description': 'Username, will always be lowercased',
            'type': 'string'
        }
        props['email'] = {
            "description": "User's email address",
            "type": "string"
        }
        props['password'] = {
            "description": "SHA256 hash of the user's password",
            "type": "string"
        }
        return schema


class Album(db.Model):
    
    __table_args__ = (db.UniqueConstraint("title", "artist", name="_album_to_artist_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    unique_name = db.Column(db.String(200), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    artist = db.Column(db.String(50), nullable=False)
    publication_date = db.Column(db.Date, nullable=True)
    duration = db.Column(db.Time, nullable=True)
    genre = db.Column(db.String(50), nullable=True)
    
    reviews = db.relationship("Review", cascade="all, delete-orphan", back_populates="album")

    def __repr__(self):
        return "{} <{}> by {}".format(self.title, self.id, self.artist)

    @staticmethod
    def get_schema():
        schema = {
            'type': 'object',
            'required': ["unique_name", "title", "artist"]
        }
        props = schema['properties'] = {}
        props['unique_name'] = {
            'description': 'Unique name for an album. Preferably title lowercased, if taken, title_artist',
            'type': 'string'
        }
        props['title'] = {
            "description": "Album title",
            "type": "string"
        }
        props['artist'] = {
            "description": "Album's artist",
            "type": "string"
        }
        props['release'] = {
            'description': 'Album\'s release date',
            'type': 'string',
            'pattern': "^[0-9]{4}-[01][0-9]-[0-3][0-9]$"
        }
        props['duration'] = {
            "description": "The length of the album in ISO 8601 time format",
            "type": "string",
            "pattern": "^[0-9][0-9]:[0-5][0-9]:[0-5][0-9]$"
        }
        props['genre'] = {
            "description": "Album's genre",
            "type": "string"
        }
        return schema


class Review(db.Model):
    
    __table_args__ = (db.UniqueConstraint("user_id", "album_id", name="_user_to_albumreview_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String, unique=True, nullable=False)
    user_id = db.Column(db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    album_id = db.Column(db.ForeignKey("album.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    star_rating = db.Column(db.Integer, nullable=False)
    submission_date = db.Column(db.DateTime, nullable=False)
    
    user = db.relationship("User", back_populates="reviews")
    album = db.relationship("Album", back_populates="reviews")
    tags = db.relationship("Tag", cascade="all, delete-orphan", back_populates="review")

    def __repr__(self):
        return "{} <{}>".format(self.title, self.id)

    @staticmethod
    def get_schema():
        schema = {
            'type': 'object',
            'required': ["user", "title", "content", "star_rating"]
        }
        props = schema['properties'] = {}
        props['user'] = {
            'description': 'Username of the reviewer',
            'type': 'string'
        }
        props['title'] = {
            "description": "Review title",
            "type": "string"
        }
        props['content'] = {
            "description": "Written content for the review",
            "type": "string"
        }
        props['star_rating'] = {
            "description": "The number of stars the reviewer gives for the album. Between 1-5",
            "type": "integer"
        }
        return schema

class Tag(db.Model):
    
    __table_args__ = (db.UniqueConstraint("user_id", "review_id", name="_usertag_to_review_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String, unique=True, nullable=False)
    user_id = db.Column(db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    review_id = db.Column(db.ForeignKey("review.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    meaning = db.Column(db.String(10), nullable=False, default="useful")
    date_created = db.Column(db.DateTime, nullable=False)
    
    user = db.relationship("User", back_populates="tags")
    review = db.relationship("Review", back_populates="tags")

    def __repr__(self):
        return "{} tag <{}> by {}".format(self.meaning, self.id, self.user.username)

    @staticmethod
    def get_schema():
        schema = {
            'type': 'object',
            'required': ['review_url', 'meaning']
        }
        props = schema['properties'] = {}
        props['review_url'] = {
            'description': 'The URL for the review for which the tag is to be added',
            'type': 'string'
        }
        props['meaning'] = {
            "description": "The meaning of the tag, either 'useful' or 'not useful'",
            "type": "string",
            "enum": ["useful", "not useful"],
            "default": "useful"
        }
        return schema


@click.command(name="init-db", help="Calls create_all() on the database")
@with_appcontext
def init_db_cmd():
    """
    Creates the actual database with the above models.
    This function is called from the command line with "$ flask init-db"
    """
    if os.path.exists("db/revmusic.db"):
        os.remove("db/revmusic.db")
    db.create_all()
    print("Database created")
