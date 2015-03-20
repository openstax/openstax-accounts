# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2015, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
from zope.interface import Interface
from pyramid.interfaces import IAuthenticationPolicy


class IOpenstaxAccounts(Interface):
    """Utility for interacting with the accounts application.
    For accounts API documentation, visit ``/api/docs/v1`` on your
    running instance of accounts.

    """

    def search(query, **kwargs):
        """See ``/api/docs/v1/application_users/index``"""

    def global_search(query):
        """See ``/api/docs/v1/users/index``"""

    def send_message(username, subject, text_body, html_body=None):
        """Sends a single message to ``username`` with ``subject`` and
        ``text_body``. If ``html_body`` is supplied that be sent as well.
        See also ``/api/docs/v1/messages/create``
        """

    def get_profile():
        """See ``/api/docs/v1/users/show``"""

    def get_profile_by_username(username):
        """See ``/api/docs/v1/application_users/find_by_username``"""

    def update_email(existing_emails, email):
        """ Unknown? """

    def update_profile(request, **post_data):
        """See ``/api/docs/v1/users/update``"""


class IOpenstaxAccountsAuthenticationPolicy(IAuthenticationPolicy):
    """Custom interface for the authentication policy."""
    # This is a separate interface so that we can specifically lookup
    # the authentication policy used with accounts. We use more than
    # one authentication policy in some of our packages, which is why
    # this interface is need.


class IMessageSender(Interface):
    """Utility for sending messages"""

    def __call__(msg_data):
        """Send the message using the given ``msg_data``."""
