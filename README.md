# PWP SPRING 2021
# RevMusic
# Group information
* Henna Kokkonen, henna.e.kokkonen@student.oulu.fi
* Tommi Järvenpää, Tommi.Jarvenpaa@student.oulu.fi

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__

## Installations

To run the application you should run the following commands (on Linux):
```bash
$ git clone https://github.com/hennas/RevMusic.git
$ cd RevMusic/
$ pip3 install -r requirements.txt
$ pip3 install .
$ export FLASK_APP=revmusic
```
**pip3 install .** is required so that the **revmusic** packages is recognized

## Initializing the DataBase

Before starting the application, you must initialize the database. This can be done by running the following command:
```bash
$ flask init-db
```
Then, you can populate the database with data by running:
```bash
$ flask populate-db
```
**Note:** A populated database can be found [here](https://github.com/hennas/RevMusic/blob/master/db/revmusic.db).

## Testing the database

The database tests can be ran with the following command:
```bash
$ python3 -m pytest tests 
# OR with coverage
$ python3 -m pytest tests --cov=revmusic
```
