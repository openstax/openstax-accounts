# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2015, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
import functools

from pyramid.security import forget
from pyramid.view import view_config
from pyramid import httpexceptions

from .interfaces import *


def authenticated_only(function):
    """Decorates a view to ensure that it can only be accessed
    by authenticated individuals.
    """
    @functools.wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.authenticated_userid:
            raise httpexceptions.HTTPUnauthorized()
        return function(request, *args, **kwargs)
    return wrapper


@view_config(route_name='login')
def login(request):
    """Redirects the user to the accounts login page."""
    # Store where we should redirect to after login
    referer = request.referer or '/'
    redirect_to = request.params.get('redirect', referer)
    if redirect_to == request.route_url('login'):
        redirect_to = '/'
    if request.unauthenticated_userid:
        return httpexceptions.HTTPFound(location=redirect_to)
    request.session.update({'redirect_to': redirect_to})
    request.authenticated_userid  # triggers login


@view_config(route_name='callback')
@authenticated_only
def callback(request):
    """Called when the user returns from accounts with authenticated
    credentials.
    """
    # callback must be protected so that effective_principals is called
    # callback must redirect
    redirect_to = '/'
    if request.session.get('redirect_to'):
        # redirect_to in session is from login
        redirect_to = request.session.pop('redirect_to')
    raise httpexceptions.HTTPFound(location=redirect_to)


@view_config(route_name='logout')
def logout(request):
    """Logs out the user from the application."""
    forget(request)
    settings = request.registry.settings
    redirects_to = settings.get(
        'openstax_accounts.logout_redirects_to', '/')
    raise httpexceptions.HTTPFound(location=redirects_to)
