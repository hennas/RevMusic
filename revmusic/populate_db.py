import click
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError

from . import db
from .db_interface import DBInterface
from .models import User, Album, Review, Tag
from .utils import to_date


# Useful link for viewing .db file contents: https://inloop.github.io/sqlite-viewer/
@click.command(name="populate-db", help="Populates the database with hardcoded data")
@with_appcontext
def populate_db_cmd():
    """
    Populates the database with example values
    """
    print("Populating the database...")
    try:
        
        DBInterface.db_add_user('admin', 'root@admin.com', '9750c9fbe856aa813c24f08b0faeba79f4f9b0d05102d4833fac8a6a5f694827')
        DBInterface.db_add_user('YTC', 'rapper@g_mail.com', '35f27d1ae747e233e966c9502427098c9d713c415a95fe47a0a855c5fecd243e')
        DBInterface.db_add_album('Iäti Vihassa ja Kunniassa', 'Vitsaus', '05-12-2004', '120', 'black metal')
        DBInterface.db_add_album('Kun Synkkä Ikuisuus Avautuu', 'Horna', genre='black metal')
        DBInterface.db_add_review(1, 1, 'Finally soome good black metal!', 'I really like this album :)', 5, '19-02-2021')
        DBInterface.db_add_review(2, 2, "I don't like black metal", 'Why am I even here?', 1, '19-02-2021')
        DBInterface.db_add_tag(1, 1, 'useful')
        DBInterface.db_add_tag(1, 2, 'not useful')
    except OperationalError:
        print('SQL Operational Error happend! Has the db been initialized?')
        return
    except IntegrityError:
        print('SQL Integrity Erroor happened! Is the db empty?')
        return
    print("Done populating!")
