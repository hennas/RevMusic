import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

# Initialize the database object
db = SQLAlchemy()

def print_lol():
    print("lol")

def create_app(test_config=None):
    """
    - This function is called when "$ flask" is entered into the command line.
    - The name "create_app" is defined in Flask's documentation, so don't change it.
    - An argument can be passed to test_config with $ export FLASK_APP="revmusic:create_app('test')"  
        - If something is passed, test.db is used instead of revmusic.db
    - Links:
        - (https://flask.palletsprojects.com/en/1.1.x/tutorial/factory/)
        - (https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/flask-api-project-layout/)
    """
    # Configure the Flask app
    app = Flask(__name__, instance_relative_config=True, static_folder="static")
    # Check what database to use
    if test_config is None:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/revmusicdb.db"
    else:
        print("Using database test.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../db/test.db"
    # Don't track modifications
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Add database to the app
    db.init_app(app)
    from . import models
    # First run $ export FLASK_APP=revmusic/__init__.py
    # Make "$ flask init-db" callable. Must be called before running the app
    app.cli.add_command(models.init_db_cmd)
    # Make "$ flask populate-db" callable.
    from . import populate_db
    app.cli.add_command(populate_db.populate_db_cmd)

    return app
