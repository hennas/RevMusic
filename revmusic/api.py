from flask import Blueprint
from flask_restful import Api

"""
This file is based on the example project
URL: https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/api.py
"""

# Import the different resources
from revmusic.resources.user import UserCollection, UserItem
from revmusic.resources.album import AlbumCollection, AlbumItem
from revmusic.resources.review import ReviewCollection, ReviewItem, ReviewsByAlbum, ReviewsByUser
#from revmusic.resources.tag import TagsByUser, TagItem

# Create the API blueprint
api_blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_blueprint)

# Add resources to the API
api.add_resource(UserCollection, '/users/')
api.add_resource(UserItem, '/users/<user>/')
api.add_resource(AlbumCollection, '/albums/')
api.add_resource(AlbumItem, '/albums/<album>/')
api.add_resource(ReviewsByAlbum, '/albums/<album>/reviews/')
api.add_resource(ReviewItem, '/albums/<album>/reviews/<review>/')
api.add_resource(ReviewCollection, '/reviews/')
api.add_resource(ReviewsByUser, '/users/<user>/reviews/')
#api.add_resource(TagsByUser, '/users/<user>/tags/')
#api.add_resource(TagItem, '/users/<user>/tags/<tag>/')
