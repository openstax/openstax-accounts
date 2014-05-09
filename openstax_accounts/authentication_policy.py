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
from pyramid.threadlocal import get_current_registry
from zope.interface import implementer

from .interfaces import *


def get_user_from_session(request):
    """Create a helper function for getting the user profile from request.user
    """
    return request.session.get('profile')


@implementer(IAuthenticationPolicy)
class OpenstaxAccountsAuthenticationPolicy(object):

    @property
    def client(self):
        if hasattr(self, '_client'):
            return self._client
        registry = get_current_registry()
        self._client = registry.getUtility(IOpenstaxAccounts)
        return self._client

    def authenticated_userid(self, request):
        me = self.client.request('/api/users/me.json')
        request.session.update({
            'profile': me,
            'username': me.get('username'),
            })
        request.session.changed()
        return me.get('username')

    def unauthenticated_userid(self, request):
        return request.session.get('username')

    def effective_principals(self, request):
        principals = [Everyone]
        if self.authenticated_userid(request):
            principals.append(Authenticated)
        return principals

    def remember(self, request, principal, **kw):
        """Remember the principal in OAuth token
        (given as keyword argument ``code``).
        The ``profile`` can optionally be given as well.
        """
        self.client.request_token_with_code(kw['code'])
        request.session.set('username', principal)
        if 'profile' in kw:
            request.session.set('profile')

    def forget(self, request):
        request.session.clear()


def main(config):
    config.add_request_method(get_user_from_session, 'user', reify=True)
    settings = config.registry.settings
    config.set_authentication_policy(OpenstaxAccountsAuthenticationPolicy(
        client=config.registry.getUtility(IOpenstaxAccounts, 'authentication'),
        application_url=settings['openstax_accounts.application_url'],
        login_path=settings['openstax_accounts.login_path'],
        callback_path=settings['openstax_accounts.callback_path'],
        logout_path=settings['openstax_accounts.logout_path'],
        ))
