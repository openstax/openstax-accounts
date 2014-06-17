# -*- coding: utf-8 -*-

import copy
from email.mime.text import MIMEText
import fnmatch
import json

from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.response import Response
from pyramid.security import Everyone, Authenticated
from pyramid.settings import aslist
from pyramid.view import view_config
from zope.interface import implementer

from .authentication_policy import get_user_from_session
from .interfaces import *


DEFAULT_PROFILE = {
    'username': 'test', # to be generated
    'id': 1, # to be generated
    'first_name': 'Test',
    'last_name': 'User',
    'contact_infos': [{
        'type': 'EmailAddress',
        'verified': True,
        'id': 1, # to b generated
        'value': '', # to be generated
        }],
    }


def get_users_from_settings(setting):
    users = {}
    for i, user in enumerate(aslist(setting, flatten=False)):
        if user.count(',') > 1:
            username, password, profile = user.split(',', 2)
            profile = json.loads(profile)
        else:
            username, password = user.split(',', 1)
            profile = copy.deepcopy(DEFAULT_PROFILE)

        if profile.get('contact_infos') is None:
            profile['contact_infos'] = [DEFAULT_PROFILE['contact_infos'][0] \
                                       .copy()]
        if not profile['contact_infos'][0]['value']:
            profile['contact_infos'][0].update({
                'id': i + 1,
                'value': '{}@example.com'.format(username)
                })

        profile['id'] = i + 1
        profile['username'] = username
        users[username] = {
            'profile': profile,
            'password': password,
                }
    return users


@implementer(IAuthenticationPolicy)
class StubAuthenticationPolicy(object):
    def __init__(self, users):
        self.users = users

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


@implementer(IOpenstaxAccounts)
class OpenstaxAccounts(object):
    def __init__(self, users):
        self.users = users

    def search(self, query):
        results = {
                'application_users': [],
                'order_by': 'username ASC',
                'users': [],
                'num_matching_users': 0,
                'per_page': 20,
                'page': 0,
                }
        for username in self.users:
            profile = self.users[username]['profile']
            values = [username]
            for key, value in profile.items():
                if key == 'contact_infos':
                    values.append(profile['contact_infos'][0]['value'])
                else:
                    values.append(value)

            for value in values:
                if fnmatch.fnmatch(username, query):
                    results['application_users'].append({
                        'application_id': 1,
                        'unread_updates': 1,
                        # this is the application user id, which we'll fake
                        'id': profile['id'] + 10,
                        'user': {
                            'username': username,
                            'id': profile['id'],
                            },
                        })
                    results['users'].append({
                        'username': username,
                        'id': profile['id'],
                        })
                    break

        # sort result by username
        results['application_users'].sort(
                lambda a, b: cmp(a['user']['username'], b['user']['username']))
        results['users'].sort(
                lambda a, b: cmp(a['username'], b['username']))
        results['num_matching_users'] = len(results['users'])

        return results


    def send_message(self, username, subject, body):
        email = None
        for user in self.users:
            if user == username:
                profile = self.users[user]['profile']
                email = profile['contact_infos'][0]['value']
        if email is None:
            raise UserNotFoundException('User "{}" not found'.format(username))

        msg = MIMEText(body)
        msg['Subject'] = '[subject prefix] {}'.format(subject)
        msg['From'] = 'openstax-accounts@localhost'
        msg['To'] = '{} <{}>'.format(username, email)
        with open('messages.txt', 'a') as f:
            f.write(msg.as_string() + '\n\n\n')


def main(config):
    config.add_request_method(get_user_from_session, 'user', reify=True)
    settings = config.registry.settings
    users = get_users_from_settings(settings.get(
        'openstax_accounts.stub.users'))

    # set authentication policy
    config.set_authentication_policy(StubAuthenticationPolicy(users))

    # add stub login form
    config.add_route('stub-login-form', '/stub-login-form')

    # register stub openstax accounts utility
    openstax_accounts = OpenstaxAccounts(users)
    config.registry.registerUtility(openstax_accounts, IOpenstaxAccounts)

    config.scan(package='openstax_accounts.stub')
