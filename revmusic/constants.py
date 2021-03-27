MASON = 'application/vnd.mason+json'
LINK_RELATIONS_URL = '/revmusic/link-relations#'

USER_PROFILE = '/profiles/user/'
ALBUM_PROFILE = '/profiles/album/'
REVIEW_PROFILE = '/profiles/review/'
TAG_PROFILE = '/profiles/tag/'
ERROR_PROFILE = '/profiles/error/'

REVIEW_ALL_SCHEMA = {
    "type": "object",
    "properties": {
        "filterby": {
            "description": "Selects the feature on which the filtering of the returned reviews should be based",
            "type": "string",
            "default": "album",
            "enum": ["album", "artist", "genre", "user"]
        },
        "searchword" : {
            "description": "Define the search word used with the filterby feature",
            "type": "string"
        },
        "timeframe" : {
            "description": "Define the timeframe in which returned reviews should have been submitted",
            "type": "string"
        },
        "nlatest" : {
            "description": "Define the number how many latest reviews should be returned",
            "type": "number"
        }
    },
    "required": []
}
