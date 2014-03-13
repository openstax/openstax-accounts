# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Everyone, Authenticated
from zope.interface import implementer

from .interfaces import *


def get_user_from_session(request):
    """Create a helper function for getting the user profile from request.user
    """
    return request.session.get('profile')


@implementer(IAuthenticationPolicy)
class OpenstaxAccountsAuthenticationPolicy(object):

    def __init__(self, client, login_path, callback_path):
        self.client = client
        self.login_path = login_path
        self.callback_path = callback_path

    def _login(self, request):
        raise HTTPFound(location=self.client.auth_uri())

    def _callback(self, request):
        code = request.params['code']
        self.client.request_token_with_code(code)

    def authenticated_userid(self, request):
        if request.path == self.login_path:
            return self._login(request)
        if request.path == self.callback_path:
            self._callback(request)
            me = self.client.request('/api/users/me.json')
            request.session.update({
                'profile': me,
                'username': me.get('username'),
                })
            request.session.changed()
            return me.get('username')
        return self.unauthenticated_userid(request)

    def unauthenticated_userid(self, request):
        return request.session.get('username')

    def effective_principals(self, request):
        groups = [Everyone]
        if self.authenticated_userid(request):
            groups.append(Authenticated)
        return groups

    def remember(self, request, principal, **kw):
        pass

    def forget(self, request):
        request.session.clear()


def main(config):
    config.add_request_method(get_user_from_session, 'user', reify=True)
    settings = config.registry.settings
    config.set_authentication_policy(OpenstaxAccountsAuthenticationPolicy(
        client=config.registry.getUtility(IOpenstaxAccounts, 'authentication'),
        login_path=settings['openstax_accounts.login_path'],
        callback_path=settings['openstax_accounts.callback_path'],
        ))
