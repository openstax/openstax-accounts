# -*- coding: utf-8 -*-

import functools
import json
import uuid

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized
from pyramid.response import Response
from pyramid.security import Authenticated, forget
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.url import route_url
from pyramid.view import view_config

from .interfaces import *

def authenticated_only(function):
    @functools.wraps(function)
    def wrapper(request, *args, **kwargs):
        if Authenticated not in request.effective_principals:
            raise HTTPUnauthorized()
        return function(request, *args, **kwargs)
    return wrapper

def menu(request):
    user = request.user
    if user:
        login_status = 'logged in'
        login_logout_path = request.route_url('logout')
        login_logout_text = 'Log out'
    else:
        login_status = 'not logged in'
        login_logout_path = request.route_url('login')
        login_logout_text = 'Log in'
    return '''
<ul>
    <li>You are currently {login_status}.</li>
    <li><a href="{hello_world_path}">Hello World!</a></li>
    <li><a href="{profile_path}">Profile</a></li>
    <li><a href="{user_search_path}">User Search</a></li>
    <li><a href="{user_search_json_path}">User Search (JSON)</a></li>
    <li><a href="{send_message_path}">Send Message</a></li>
    <li><a href="{login_logout_path}">{login_logout_text}</a></li>
</ul>'''.format(
        login_status=login_status,
        hello_world_path=request.route_url('hello-world'),
        login_logout_path=login_logout_path,
        login_logout_text=login_logout_text,
        profile_path=request.route_url('profile'),
        user_search_path=request.route_url('user-search', format=''),
        user_search_json_path=request.route_url('user-search', format='.json'),
        send_message_path=request.route_url('send-message'),
        )

@view_config(route_name='index')
def index(request):
    return Response(menu(request))

@view_config(route_name='hello-world')
def hello_world(request):
    return Response(menu(request) + '<p>Hello world!</p>')

@view_config(route_name='profile', request_method='GET')
@authenticated_only
def profile(request):
    user = request.user
    profile = '<ul>' + ''.join([
        '<li><strong>{}</strong>: {}</li>'.format(k, v)
        for k, v in user.items()]) + '</ul>'
    email = ''
    if user.get('contact_infos'):
        for contact_info in user['contact_infos']:
            if contact_info['type'] == 'EmailAddress':
                email = contact_info['value']
    profile_form = '''
<form method="post">
    <div>
        <label for="first-name">First Name:</label>
        <input id="first-name" name="first_name" value="{first_name}" />
    </div>
    <div>
        <label for="last-name">Last Name:</label>
        <input id="last-name" name="last_name" value="{last_name}" />
    </div>
    <div>
        <label for="full-name">Full Name:</label>
        <input id="full-name" name="full_name" value="{full_name}" />
    </div>
    <div>
        <label for="email">Email:</label>
        <input id="email" name="email" value="{email}" />
    </div>
    <input name="submit" type="submit" />
</form>
'''.format(email=email, first_name=user.get('first_name', ''),
           last_name=user.get('last_name', ''),
           full_name=user.get('full_name', ''))
    return Response(menu(request) + '<p>Profile</p>' + profile + profile_form)

@view_config(route_name='profile', request_method='POST')
@authenticated_only
def post_profile(request):
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    full_name = request.POST['full_name']
    email = request.POST['email']
    request.accounts_client.update_profile(request, **request.POST)
    return Response(menu(request) + '<p>Profile updated</p>')

@view_config(route_name='user-search')
@authenticated_only
def user_search(request):
    util = request.registry.getUtility(IOpenstaxAccounts)
    users = util.search('%', order_by='first_name,last_name')
    if request.matchdict.get('format') == '.json':
        return Response(json.dumps(users), content_type='application/json')
    return Response(menu(request) + '<p>User Search</p>{}'.format(users))

@view_config(route_name='send-message')
@authenticated_only
def send_message(request):
    if request.method == 'GET':
        return Response(menu(request) + '''\
                <p>Send a message</p>
                <form method="post" action="">
                    <label for="username">Username:</label>
                    <input id="username" name="username" />
                    <label for="subject">Subject:</label>
                    <input id="subject" name="subject" />
                    <label for="body">Body:</label>
                    <textarea id="body" name="body"></textarea>
                    <input type="submit" />
                </form>\n''')

    username = request.params['username']
    subject = request.params['subject']
    body = request.params['body']
    util = request.registry.getUtility(IOpenstaxAccounts)
    util.send_message(username, subject, body)
    return Response(menu(request) + '<p>Message sent</p>')

@view_config(route_name='callback')
@authenticated_only
def callback(request):
    # callback must redirect
    return HTTPFound(location='/')

@view_config(route_name='login')
@authenticated_only
def login(request):
    pass

@view_config(route_name='logout')
def logout(request):
    forget(request)
    raise HTTPFound(location='/')

def main(global_config, **settings):
    session_factory = UnencryptedCookieSessionFactoryConfig(
            str(uuid.uuid4()))

    config = Configurator(settings=settings,
                          session_factory=session_factory)
    config.add_route('index', '/')
    config.add_route('hello-world', '/hello-world')
    config.add_route('profile', '/profile')
    config.add_route('user-search', '/users/search{format:(.json)?}')
    config.add_route('send-message', '/message')
    config.add_route('callback', '/callback')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.scan(package='openstax_accounts.example')
    config.include('openstax_accounts.main')

    # authorization policy must be set if an authentication policy is set
    config.set_authentication_policy(
            config.registry.getUtility(IOpenstaxAccountsAuthenticationPolicy))
    config.set_authorization_policy(ACLAuthorizationPolicy())
    return config.make_wsgi_app()
