import datetime
from .models import User, Album, Review, Tag


def to_date(date_str):
    """
    Convert a "%YYYY-%mm-%dd" string to a Date
    params:
    - date_str: The date string
    Returns: Date or None if failed to convert. None is also returned if date_str is None
    """
    if date_str is None:
        return None
    try:
        y, m, d = date_str.split('-')
        return datetime.date(int(y), int(m), int(d))
    except (IndexError, ValueError) as e:
        #print("Incorrect date format: {}".format(date_str))
        return None

def to_datetime(datetime_str):
    """
    Convert a "%YYYY-%mm-%dd %HH:%MM:%SS" string to a Date
    params:
    - datetime_str: The datetime string
    Returns: Datetime or None if failed to convert. None is also returned if datetime_str is None
    """
    try:
        return datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except:
        #print("Incorrect datetime format: {}".format(datetime_str))
        return None

def to_time(time_str):
    """
    Convert a "%HH:%MM:%SS" string to a Time
    params:
    - time_str: The time string
    Returns: Time or None if failed to convert. None is also returned if time_str is None
    """
    if time_str is None:
        return None
    try:
        h, m, s = time_str.split(':')
        return datetime.time(int(h), int(m), int(s))
    except (IndexError, ValueError) as e:
        #print("Incorrect time format: {}".format(time_str))
        return None

def to_user(username, email, password):
    return User(
        username=username,
        email=email,
        password=password
    )

def to_album(unique_name, title, artist, publication_date, duration, genre):
    return Album(
        unique_name=unique_name,
        title=title,
        artist=artist,
        publication_date=publication_date,
        duration=duration,
        genre=genre
    )

def to_review(identifier, title, content, star_rating, submission_date):
    return Review(
        identifier=identifier,
        title=title,
        content=content,
        star_rating=star_rating,
        submission_date=submission_date
    )

def to_tag(identifier, meaning, date_created):
    return Tag(
        identifier=identifier,
        meaning=meaning,
        date_created=date_created
    )

class MasonBuilder(dict):
    """
    Taken from the example project.
    URL: https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/utils.py
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.
        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.
        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.
        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.
        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

def create_error_response(status_code, title, message=None):
    """
    Taken from the example project.
    URL: https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/utils.py
    """
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)