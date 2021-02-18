from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///revmusicdb.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    
class User(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    
    reviews = db.relationship("Review", cascade="all, delete-orphan", back_populates="user")
    tags = db.relationship("Tag", cascade="all, delete-orphan", back_populates="user")
    
    def __repr__(self):
        return "{} <{}>".format(self.username, self.id)
        
class Album(db.Model):
    
    __table_args__ = (db.UniqueConstraint("title", "artist", name="_album_to_artist_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    artist = db.Column(db.String(50), nullable=False)
    publication_date = db.Column(db.Date, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    genre = db.Column(db.String(50), nullable=True)
    
    reviews = db.relationship("Review", cascade="all, delete-orphan", back_populates="album")

    def __repr__(self):
        return "{} <{}> by {}".format(self.title, self.id, self.artist)
        
class Review(db.Model):
    
    __table_args__ = (db.UniqueConstraint("user_id", "album_id", name="_user_to_albumreview_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    album_id = db.Column(db.ForeignKey("album.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    star_rating = db.Column(db.Integer, nullable=False)
    submission_date = db.Column(db.Date, nullable=False)
    
    user = db.relationship("User", back_populates="reviews")
    album = db.relationship("Album", back_populates="reviews")
    tags = db.relationship("Tag", cascade="all, delete-orphan", back_populates="review")

    def __repr__(self):
        return "{} <{}>".format(self.title, self.id)
    
class Tag(db.Model):
    
    __table_args__ = (db.UniqueConstraint("user_id", "review_id", name="_usertag_to_review_uc"), )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    review_id = db.Column(db.ForeignKey("review.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    meaning = db.Column(db.String(10), nullable=False, default="useful")
    
    user = db.relationship("User", back_populates="tags")
    review = db.relationship("Review", back_populates="tags")
