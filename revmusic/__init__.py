import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

# Initialize the database object
db = SQLAlchemy()

# The example project provided by the course assistants was a basis for this
def create_app(test_config=None):
    """
    - This function is called when "$ flask" is entered into the command line.
    - The name "create_app" is defined in Flask's documentation, so don't change it. 
    - Links:
        - (https://flask.palletsprojects.com/en/1.1.x/tutorial/factory/)
        - (https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/flask-api-project-layout/)
    """
    # Configure the Flask app
    app = Flask(__name__, instance_relative_config=True, static_folder="static")
    # Check what database to use
    if test_config is None:
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI = "sqlite:///../db/revmusic.db",
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
    else:
        app.config.from_mapping(test_config)

    # Add database to the app
    db.init_app(app)
    # Force foreing key usage
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    from . import models
    # First run $ export FLASK_APP=revmusic/__init__.py
    # Make "$ flask init-db" callable. Must be called before running the app
    app.cli.add_command(models.init_db_cmd)
    # Make "$ flask populate-db" callable.
    from . import populate_db
    app.cli.add_command(populate_db.populate_db_cmd)

    return app
