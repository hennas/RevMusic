# PWP SPRING 2021
# RevMusic

## Installations

**Note: This must be done before tests can be run! Virtual environment recommended.**

To run the application you should run the following commands (on Linux):
```bash
$ git clone https://github.com/hennas/RevMusic.git
$ cd RevMusic/
$ pip3 install -r requirements.txt
$ pip3 install .
$ export FLASK_APP=revmusic
```
**pip3 install .** is required so that the **revmusic** package is recognized

#### Dependencies
```
click==6.7
Flask==1.1.2
Flask-SQLAlchemy==2.4.1
Flask-RESTful==0.3.6
SQLAlchemy==1.3.16
jsonschema
pytest==5.4.2
pytest-cov==2.8.
flask-cors
```

## Initializing the DataBase

**Note: This initializes the database for the app, and adds some data to it. The db file already exists, and can be found [here](https://github.com/hennas/RevMusic/blob/master/db/revmusic.db). The database we use is SQLite 3.x**

Before starting the application, you must initialize the database. This can be done by running the following command:
```bash
$ flask init-db
```
Then, you can populate the database with data by running:
```bash
$ flask populate-db
```

## Running the Application
Once you have installed everything and initialized the database, run this command:
```bash
$ flask run
```
The API can now be found [here](http://127.0.0.1:5000/api/)

## Running the Client
When you have the database and the Flask API running, the client can be started with:
```bash
python3 client.py
```
The client front end can now be found [here](http://127.0.0.1:5001)

## Running the Tests

The tests can be ran with the following commands:
```bash
$ python3 -m pytest -s tests 
# OR with coverage
$ python3 -m pytest tests --cov=revmusic
```
This runs the tests for both, the database and the API. If you want to run them individually, change tests to **tests/test_db.py** or **tests/test_api.py**.
