from flask import Response, request, url_for
import json

from revmusic.models import *
from revmusic.constants import *

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

class RevMusicBuilder(MasonBuilder):
    ###
    # USERS
    ###
    def add_control_users_all(self, ctrl='revmusic:users-all'):
        """
        revmusic:users-all
        """
        self.add_control(
            ctrl,
            href=url_for('api.usercollection'),
            title='All users',
            method='GET'
        )

    def add_control_add_user(self):
        """
        revmusic:add-user
        """
        self.add_control(
            'revmusic:add-user',
            href=url_for('api.usercollection'),
            title='Add a new user',
            encoding='json',
            method='POST',
            schema=User.get_schema()
        )

    def add_control_edit_user(self, user):
        """
        edit
        """
        self.add_control(
            'edit',
            href=url_for('api.useritem', user=user),
            title='Edit this user',
            encoding='json',
            method='PUT',
            schema=User.get_schema()
        )

    def add_control_delete_user(self, user):
        """
        revmusic:delete
        """
        self.add_control(
            'revmusic:delete',
            href=url_for('api.useritem', user=user),
            title='Delete this user',
            method='DELETE'
        )

    ###
    # ALBUMS
    ###

    def add_control_albums_all(self):
        """
        revmusic:albums-all
        """
        self.add_control(
            'revmusic:albums-all',
            href=url_for('api.albumcollection'),
            title='All albums',
            method='GET'           
        )

    def add_control_add_album(self):
        """
        revmusic:add-user
        """
        self.add_control(
            'revmusic:add-album',
            href=url_for('api.albumcollection'),
            title='Add a new album',
            encoding='json',
            method='POST',
            schema=Album.get_schema()
        )

    def add_control_edit_album(self, album):
        """
        edit
        """
        self.add_control(
            'edit',
            href=url_for('api.albumitem', album=album),
            title='Edit this album',
            encoding='json',
            method='PUT',
            schema=Album.get_schema()
        )
        
    def add_control_delete_album(self, album):
        """
        revmusic:delete
        """
        self.add_control(
            'revmusic:delete',
            href=url_for('api.albumitem', album=album),
            title='Delete this album',
            method='DELETE'
        )
        
    ###
    # REVIEWS
    ###

    def add_control_reviews_all(self, ctrl='revmusic:reviews-all'):
        """
        revmusic:reviews-all
        """
        self.add_control(
            ctrl,
            href=url_for('api.reviewcollection') + '?{filterby,searchword,timeframe,nlatest}',
            title='All reviews',
            method='GET',
            isHrefTemplate=True,
            schema=REVIEW_ALL_SCHEMA
        )

    def add_control_reviews_by(self, user, ctrl='revmusic:reviews-by'):
        """
        revmusic:reviews-by
        """
        self.add_control(
            ctrl,
            href=url_for('api.reviewsbyuser', user=user),
            title='All reviews submitted by the user'
        )
        
    def add_control_reviews_for(self, album, ctrl='revmusic:reviews-for'):
        """
        revmusic:reviews-for
        """
        self.add_control(
            ctrl,
            href=url_for('api.reviewsbyalbum', album=album),
            title='All reviews submitted for the album'
        )
        
    def add_control_add_review(self, album):
        """
        revmusic:add-review
        """
        self.add_control(
            'revmusic:add-review',
            href=url_for('api.reviewsbyalbum', album=album),
            title='Add a new review for this album',
            encoding='json',
            method='POST',
            schema=Review.get_schema()
        )
        
    def add_control_edit_review(self, album, review):
        """
        edit
        """
        self.add_control(
            'edit',
            href=url_for('api.reviewitem', album=album, review=review),
            title='Edit this review',
            encoding='json',
            method='PUT',
            schema=Review.get_schema()
        )
        
    def add_control_delete_review(self, album, review):
        """
        revmusic:delete
        """
        self.add_control(
            'revmusic:delete',
            href=url_for('api.reviewitem', album=album, review=review),
            title='Delete this review',
            method='DELETE'
        )
