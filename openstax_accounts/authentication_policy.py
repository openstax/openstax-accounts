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
from pyramid.settings import aslist
from zope.interface import implementer

from .interfaces import *
from .utils import local_settings


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


@implementer(IOpenstaxAccountsAuthenticationPolicy)
class OpenstaxAccountsAuthenticationPolicy(object):

    def __init__(self, application_url, login_path, callback_path, logout_path):
        self.application_url = application_url
        self.login_path = login_path
        self.callback_path = callback_path
        self.logout_path = logout_path

    def _login(self, request):
        raise HTTPFound(location=request.accounts_client.auth_uri())

    def _groups(self, request):
        """A mapping of group ids a list of user ids"""
        # TODO Ideally, we'd use the accounts groups, but the implementation
        #      of groups in accounts is not fleshed out enough at this time.
        #      So for now we pull them from configuration settings.
        if not hasattr(self, '_parsed_groups'):
            self._parsed_groups = {}
            settings = request.registry.settings
            prefix = 'openstax_accounts.groups'
            groups = local_settings(settings, prefix=prefix)
            for group_name, values in groups.items():
                self._parsed_groups[group_name] = aslist(values)
        return self._parsed_groups

    def _membership(self, request, userid):
        """List of groups this `userid` has membership with."""
        return [group_name
                for group_name, userids in self._groups(request).items()
                if userid in userids]

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
            groups.append('u:{}'.format(userid))
        groups.extend(['g:{}'.format(name)
                       for name in self._membership(request, userid)])
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


# BBB (11-Mar-2015) Deprecated, use 'includeme' by invoking
#     ``config.include('openstax_accounts')``.
def main(config):
    includeme(config)


def includeme(config):
    config.add_request_method(get_user_from_session, 'user', reify=True)
    config.add_request_method(get_accounts_client, 'accounts_client',
                              reify=True)
    settings = config.registry.settings
    settings = local_settings(settings)
    config.registry.registerUtility(OpenstaxAccountsAuthenticationPolicy(
        application_url=settings['application_url'],
        login_path=settings['login_path'],
        callback_path=settings['callback_path'],
        logout_path=settings['logout_path'],
        ), IOpenstaxAccountsAuthenticationPolicy)
