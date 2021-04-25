import os
import json
from flask_cors import CORS
from flask import Flask, Response, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event

# Initialize the database object
db = SQLAlchemy()

from .constants import *

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
    # SOURCE: https://stackoverflow.com/questions/65587708/why-is-flask-cors-not-detecting-my-cross-origin-domain-in-production
    CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": "*", "expose_headers": "*"}})
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
    # Force foreing key usageUserCo
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    # Make "$ flask init-db" callable. Must be called before running the app
    from . import models
    app.cli.add_command(models.init_db_cmd)
    # Make "$ flask populate-db" callable.
    from . import populate_db
    app.cli.add_command(populate_db.populate_db_cmd)

    # Register API blueprint
    from . import api
    app.register_blueprint(api.api_blueprint) 

    # Set link relations URL
    @app.route(LINK_RELATIONS_URL)
    def send_link_relations():
        return redirect(APIARY_URL + "link-relations")
        
    # Set profiles URL
    @app.route('/profiles/<profile>/')
    def send_profile(profile):
        return redirect(APIARY_URL + "profiles")


    from revmusic.mason import RevMusicBuilder
    # Add entry point
    @app.route('/api/', methods=["GET"])
    def entry_point():
        """
        Returns Mason with the controls:
        - revmusic:reviews-all
        - revmusic:albums-all
        - revmusic:users-all
        """    
        body = RevMusicBuilder()
        body.add_namespace('revmusic', LINK_RELATIONS_URL)
        body.add_control_reviews_all()
        body.add_control_albums_all()
        body.add_control_users_all()
        return Response(json.dumps(body), 200, mimetype=MASON)

    return app
