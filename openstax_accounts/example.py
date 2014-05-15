# -*- coding: utf-8 -*-

import functools
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
    <li><a href="{login_logout_path}">{login_logout_text}</a></li>
</ul>'''.format(
        login_status=login_status,
        hello_world_path=request.route_url('hello-world'),
        login_logout_path=login_logout_path,
        login_logout_text=login_logout_text,
        profile_path=request.route_url('profile'),
        user_search_path=request.route_url('user-search'),
        )

@view_config(route_name='index')
def index(request):
    return Response(menu(request))

@view_config(route_name='hello-world')
def hello_world(request):
    return Response(menu(request) + '<p>Hello world!</p>')

@view_config(route_name='profile')
@authenticated_only
def profile(request):
    user = request.user
    profile = '<ul>' + ''.join([
        '<li><strong>{}</strong>: {}</li>'.format(k, v)
        for k, v in user.items()]) + '</ul>'
    return Response(menu(request) + '<p>Profile</p>' + profile)

@view_config(route_name='user-search')
@authenticated_only
def user_search(request):
    users = request.registry.getUtility(IOpenstaxAccounts).request('/api/application_users.json?q=*')
    return Response(menu(request) + '<p>User Search</p>{}'.format(users))

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
    config.add_route('user-search', '/users/search')
    config.add_route('callback', '/callback')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.scan(ignore='openstax_accounts.tests')

    # use the openstax accounts authentication policy
    config.include('openstax_accounts.openstax_accounts.main')
    config.include('openstax_accounts.authentication_policy.main')

    # authorization policy must be set if an authentication policy is set
    config.set_authorization_policy(ACLAuthorizationPolicy())
    return config.make_wsgi_app()
