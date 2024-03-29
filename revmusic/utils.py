import datetime

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

def create_identifier(prefix):
    """
    Creates an identifier for an item: takes current datetime, stringifies it by concatenating year, month, day, hours, minutes and seconds,
    and adds this combination to a given prefix. Returns the identifier and the creation datetime as a tuple.
    : param str prefix: Prefix of an identifier, e.g., "review_"
    """
    dt = datetime.datetime.now()
    dt_str = dt.strftime("%Y%m%d%H%M%S")
    identifier = prefix + dt_str
    return (identifier, dt)
