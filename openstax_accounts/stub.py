# -*- coding: utf-8 -*-

import copy
import json

from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.response import Response
from pyramid.security import Everyone, Authenticated
from pyramid.settings import aslist
from pyramid.view import view_config
from zope.interface import implementer

from .authentication_policy import get_user_from_session


DEFAULT_PROFILE = {
    'username': 'test', # to be generated
    'id': 1, # to be generated
    'first_name': 'Test',
    'last_name': 'User',
    'contact_infos': [{
        'type': 'EmailAddress',
        'verified': True,
        'id': 1,
        'value': 'test@example.com',
        }],
    }


@implementer(IAuthenticationPolicy)
class StubAuthenticationPolicy(object):
    def __init__(self, users):
        self.users = {}
        for i, user in enumerate(aslist(users, flatten=False)):
            if user.count(',') > 1:
                username, password, profile = user.split(',', 2)
                profile = json.loads(profile)
            else:
                username, password = user.split(',')
                profile = copy.deepcopy(DEFAULT_PROFILE)
                profile['contact_infos'][0].update({
                    'id': i + 1,
                    'value': '{}@example.com'.format(username)
                    })
            profile['id'] = i + 1
            profile['username'] = username
            self.users[username] = {
                    'profile': profile,
                    'password': password,
                    }

    def authenticated_userid(self, request):
        settings = request.registry.settings
        login_path = settings['openstax_accounts.login_path']
        callback_path = settings['openstax_accounts.callback_path']
        if request.path == login_path:
            raise HTTPFound(location=request.route_url('stub-login-form'))
        if request.path == callback_path:
            return self.unauthenticated_userid(request)

        username = request.params.get('username')
        password = request.params.get('password')
        user = self.users.get(username)
        if user and user['password'] == password:
            self.remember(request, username, profile=user['profile'])
            return username
        return self.unauthenticated_userid(request)

    def unauthenticated_userid(self, request):
        return request.session.get('username')

    def effective_principals(self, request):
        principals = [Everyone]
        userid = self.authenticated_userid(request)
        if userid:
            principals.append(Authenticated)
            principals.append(userid)
        return principals

    def remember(self, request, principal, **kw):
        request.session.update({
            'username': principal,
            'profile': kw.get('profile'),
            })
        request.session.changed()

    def forget(self, request):
        request.session.clear()


@view_config(route_name='stub-login-form', request_method=['GET', 'POST'])
def login_form(request):
    error = ''
    if request.method == 'POST':
        if request.authenticated_userid:
            raise HTTPFound(request.registry.settings[
                'openstax_accounts.callback_path'])
        error = 'Username or password incorrect'
    return Response('''\
<html>
<body>
    <div>{error}</div>
    <form method="POST" action="">
        <div>
            <label for="username">Username:</label>
            <input name="username" id="username" />
        </div>
        <div>
            <label for="password">Password:</label>
            <input name="password" type="password" id="password" />
        </div>
        <div>
            <input type="submit" />
        </div>
    </form>
</body>
</html>
    '''.format(error=error))


def main(config):
    config.add_request_method(get_user_from_session, 'user', reify=True)
    settings = config.registry.settings
    config.set_authentication_policy(StubAuthenticationPolicy(
        users=settings.get('openstax_accounts.stub.users'),
        ))
    config.add_route('stub-login-form', '/stub-login-form')
    config.scan(package='openstax_accounts.stub')
