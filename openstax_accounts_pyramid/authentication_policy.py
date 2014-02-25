# -*- coding: utf-8 -*-

import json
import urlparse
import uuid

from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Everyone, Authenticated
import sanction
from zope.interface import implements


def get_user_from_session(request):
    """Create a helper function for getting the user profile from request.user
    """
    return request.session.get('profile')


class OpenstaxAccountsAuthenticationPolicy(object):
    implements(IAuthenticationPolicy)

    def __init__(self, server_url, application_id, application_secret,
            application_url, login_path, callback_path):
        resource_url = server_url
        authorize_url = urlparse.urljoin(server_url, '/oauth/authorize')
        token_url = urlparse.urljoin(server_url, '/oauth/token')
        self.redirect_uri = urlparse.urljoin(application_url, '/callback')

        self.sanction_client = sanction.Client(
                auth_endpoint=authorize_url,
                token_endpoint=token_url,
                resource_endpoint=resource_url,
                client_id=application_id,
                client_secret=application_secret)

        self.login_path = login_path
        self.callback_path = callback_path

    def _login(self, request):
        raise HTTPFound(location=self.sanction_client.auth_uri(redirect_uri=self.redirect_uri))

    def _callback(self, request):
        code = request.params['code']
        def parser_remove_null_expires_in(data):
            data = json.loads(data)
            if data.get('expires_in', '') is None:
                data.pop('expires_in')
            return data

        self.sanction_client.request_token(
                parser=parser_remove_null_expires_in,
                code=code,
                redirect_uri=self.redirect_uri)

    def authenticated_userid(self, request):
        if request.path == self.login_path:
            return self._login(request)
        if request.path == self.callback_path:
            self._callback(request)
            me = self.sanction_client.request('/api/v1/me.json')
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
        server_url=settings['openstax_accounts.server_url'],
        application_id=settings['openstax_accounts.application_id'],
        application_secret=settings['openstax_accounts.application_secret'],
        application_url=settings['openstax_accounts.application_url'],
        login_path=settings['openstax_accounts.login_path'],
        callback_path=settings['openstax_accounts.callback_path'],
        ))
