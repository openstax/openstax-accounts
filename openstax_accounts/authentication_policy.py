# -*- coding: utf-8 -*-

try:
    import urlparse # python2
except ImportError:
    import urllib.parse as urlparse # renamed in python3
try:
    from urllib import urlencode # python2
except ImportError:
    from urllib.parse import urlencode # moved in python3

from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Everyone, Authenticated
from zope.interface import implementer

from .interfaces import *


def get_user_from_session(request):
    """Create a helper function for getting the user profile from request.user
    """
    return request.session.get('profile')


def get_accounts_client(request):
    """Create a helper function for returning an accounts client
    with the user's access token
    """
    client = request.registry.getUtility(IOpenstaxAccounts, 'factory')()
    access_token = request.session.get('access_token')
    if access_token:
        client.access_token = access_token
    return client


@implementer(IAuthenticationPolicy)
class OpenstaxAccountsAuthenticationPolicy(object):

    def __init__(self, application_url, login_path, callback_path, logout_path):
        self.application_url = application_url
        self.login_path = login_path
        self.callback_path = callback_path
        self.logout_path = logout_path

    def _login(self, request):
        raise HTTPFound(location=request.accounts_client.auth_uri())

    def authenticated_userid(self, request):
        if request.path == self.login_path:
            return self._login(request)
        if request.path == self.callback_path:
            code = request.params['code']
            request.accounts_client.request_token_with_code(code)
            me = request.accounts_client.get_profile()
            request.session.update({
                'profile': me,
                'username': me.get('username'),
                'access_token': request.accounts_client.access_token,
                })
            request.session.changed()
            return me.get('username')
        return self.unauthenticated_userid(request)

    def unauthenticated_userid(self, request):
        return request.session.get('username')

    def effective_principals(self, request):
        groups = [Everyone]
        userid = self.authenticated_userid(request)
        if userid:
            groups.append(Authenticated)
            groups.append(userid)
        return groups

    def remember(self, request, principal, **kw):
        pass

    def forget(self, request):
        if self.unauthenticated_userid(request):
            logout_url = urlparse.urljoin(request.accounts_client.server_url,
                                          '/logout')
            return_to = urlparse.urljoin(self.application_url, self.logout_path)
            params = urlencode({'return_to': return_to})
            request.session.clear()
            raise HTTPFound(location='?'.join([logout_url, params]))


def main(config):
    config.add_request_method(get_user_from_session, 'user', reify=True)
    config.add_request_method(get_accounts_client, 'accounts_client',
                              reify=True)
    settings = config.registry.settings
    config.registry.registerUtility(OpenstaxAccountsAuthenticationPolicy(
        application_url=settings['openstax_accounts.application_url'],
        login_path=settings['openstax_accounts.login_path'],
        callback_path=settings['openstax_accounts.callback_path'],
        logout_path=settings['openstax_accounts.logout_path'],
        ), IOpenstaxAccountsAuthenticationPolicy)
