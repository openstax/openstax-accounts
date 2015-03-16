# -*- coding: utf-8 -*-
from pyramid.settings import asbool

from .utils import local_settings


# BBB (11-Mar-2015) Deprecated, use 'includeme' by invoking
#     ``config.include('openstax_accounts')``.
def main(config):
    includeme(config)


def declare_oauth_routes(config):
    """Declaration of routing for oauth"""
    settings = config.registry.settings
    settings = local_settings(settings)
    login_path = settings['login_path']
    callback_path = settings['callback_path']
    logout_path = settings['logout_path']

    add_route = config.add_route
    add_route('login', login_path, request_method='GET')
    add_route('callback', callback_path, request_method='GET')
    add_route('logout', logout_path, request_method='GET')


def includeme(config):
    """Includes this package into a pyramid application."""
    settings = config.registry.settings
    settings = local_settings(settings)

    # Disable SSL certificate verification added in python 2.7.9
    # See https://bugs.python.org/issue22417
    if asbool(settings.get('disable_verify_ssl')):
        import ssl
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context

    if asbool(settings.get('stub')):
        # Use the stub authentication policy
        config.include('openstax_accounts.stub')
    else:
        # use the openstax accounts authentication policy
        config.include('openstax_accounts.openstax_accounts')
        config.include('openstax_accounts.authentication_policy')
