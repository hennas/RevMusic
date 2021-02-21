import datetime


def to_date(date_str):
    """
    Convert a "%dd-%mm-%YYYY" string to a Date
    params:
    - date_str: The date string
    Returns: Date or None if failed to convert. None is also returned if date_str is None
    """
    if date_str is None:
        return None
    try:
        d, m, y = date_str.split('-')
        return datetime.date(int(y), int(m), int(d))
    except (IndexError, ValueError) as e:
        print("Incorrect date format: {}".format(date_str))
        return None
