# -*- coding: utf-8 -*-

import cgi
import json
import urllib
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode # python3
try:
    import urlparse # python2
except ImportError:
    import urllib.parse as urlparse # renamed in python3

import sanction
from zope.interface import implementer

from .interfaces import *

# A json parser for data returned from a request_token request because sanction
# does not work with a null expires_in
def parser_remove_null_expires_in(data):
    data = json.loads(data)
    if data.get('expires_in', '') is None:
        data.pop('expires_in')
    return data

class UserNotFoundException(Exception):
    pass


@implementer(IOpenstaxAccounts)
class OpenstaxAccounts(object):

    def __init__(self, server_url, application_id, application_secret,
            application_url):
        self.server_url = server_url
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

    def auth_uri(self):
        return self.sanction_client.auth_uri(redirect_uri=self.redirect_uri)

    def request_token_with_code(self, code):
        self.sanction_client.request_token(
                code=code,
                redirect_uri=self.redirect_uri,
                parser=parser_remove_null_expires_in)

    def request_application_token(self):
        self.sanction_client.request_token(
                grant_type='client_credentials',
                parser=parser_remove_null_expires_in)

    def request(self, *args, **kwargs):
        return self.sanction_client.request(*args, **kwargs)

    def search(self, query):
        return self.request('/api/application_users.json?{}'.format(
            urlencode({'q': query})))

    def send_message(self, username, subject, body):
        users = self.search('username:{}'.format(username))
        userid = None
        for user in users['users']:
            if user['username'] == username:
                userid = user['id']
        if userid is None:
            raise UserNotFoundException('User "{}" not found'.format(username))

        self.request('/api/messages.json', data=urlencode({
                     'user_id': int(userid),
                     'to[user_ids][]': [int(userid)],
                     'subject': subject,
                     'body[text]': body,
                     'body[html]': '<html><body>{}</body></html>'.format(
                         cgi.escape(body)),
                     }, True))


def main(config):
    settings = config.registry.settings
    server_url = settings['openstax_accounts.server_url']
    application_id = settings['openstax_accounts.application_id']
    application_secret = settings['openstax_accounts.application_secret']
    application_url = settings['openstax_accounts.application_url']

    args = (server_url, application_id, application_secret, application_url)

    openstax_accounts = OpenstaxAccounts(*args)
    openstax_accounts.request_application_token()
    config.registry.registerUtility(openstax_accounts, IOpenstaxAccounts)

    config.registry.registerUtility(OpenstaxAccounts, IOpenstaxAccounts,
            name='factory')
