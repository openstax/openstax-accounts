# -*- coding: utf-8 -*-

import cgi
import json
import logging
import urllib
import pprint
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode # python3
try:
    import urlparse # python2
except ImportError:
    import urllib.parse as urlparse # renamed in python3

import sanction
from pyramid.threadlocal import get_current_registry
from zope.interface import implementer

from .interfaces import *


logger = logging.getLogger('openstax-accounts')


class UserNotFoundException(Exception):
    pass


# A json parser for data returned from a request_token request because sanction
# does not work with a null expires_in
def parser_remove_null_expires_in(data):
    data = json.loads(data)
    if data.get('expires_in', '') is None:
        data.pop('expires_in')
    return data


@implementer(IMessageSender)
def send_message(msg_data):
    """Send the message using the accounts request."""
    accounts = get_current_registry().getUtility(IOpenstaxAccounts)
    accounts.request('/api/messages.json', data=urlencode(msg_data, True))


@implementer(IMessageSender)
def log_message(msg_data):
    """Log the message to the local logger."""
    msg_data_as_str = pprint.pformat(msg_data)
    logger.info("Captured message:\n\n{}".format(msg_data_as_str))


@implementer(IOpenstaxAccounts)
class OpenstaxAccounts(object):

    server_url = None
    application_id = None
    application_secret = None
    application_url = None

    def __init__(self, server_url=None, application_id=None,
                 application_secret=None, application_url=None):
        if server_url:
            self.server_url = server_url
        if application_id:
            self.application_id = application_id
        if application_secret:
            self.application_secret = application_secret
        if application_url:
            self.application_url = application_url

        resource_url = self.server_url
        authorize_url = urlparse.urljoin(self.server_url, '/oauth/authorize')
        token_url = urlparse.urljoin(self.server_url, '/oauth/token')
        self.redirect_uri = urlparse.urljoin(self.application_url, '/callback')

        self.sanction_client = sanction.Client(
                auth_endpoint=authorize_url,
                token_endpoint=token_url,
                resource_endpoint=resource_url,
                client_id=self.application_id,
                client_secret=self.application_secret)

    @property
    def access_token(self):
        return self.sanction_client.access_token

    @access_token.setter
    def access_token(self, access_token):
        self.sanction_client.access_token = access_token

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

    def search(self, query, **kwargs):
        kwargs['q'] = query
        return self.request('/api/application_users.json?{}'.format(
            urlencode(kwargs)))

    def global_search(self, query):
        return self.request('/api/users.json?{}'.format(
            urlencode({'q': query})))

    def send_message(self, username, subject, text_body, html_body=None):
        users = self.global_search('username:{}'.format(username))
        userid = None
        for user in users['items']:
            if user['username'] == username:
                userid = user['id']
        if userid is None:
            raise UserNotFoundException('User "{}" not found'.format(username))

        if html_body is None:
            html_body = '<html><body>{}</body></html>'.format(
                cgi.escape(text_body).replace('\n', '\n<br/>'))

        msg_data = {
            'user_id': int(userid),
            'to[user_ids][]': [int(userid)],
            'subject': subject,
            'body[text]': text_body,
            'body[html]': html_body,
            }

        send_msg_util = get_current_registry().getUtility(IMessageSender)
        send_msg_util(msg_data)

    def get_profile(self):
        return self.request('/api/user.json')

    def update_email(self, existing_emails, email):
        for email in existing_emails:
            self.request('/api/contact_infos/{}'.format(email['id']))
        contact_info = self.request('/api/contact_infos.json',
                                    data=json.dumps({
                                        'type': 'EmailAddress',
                                        'value': email,
                                        }))

    def update_profile(self, request, **post_data):
        emails = [i for i in request.user.get('contact_infos', [])
                  if i['type'] == 'EmailAddress']
        # separate api for updating email address
        if post_data.get('email') and post_data['email'] not in emails:
            self.update_email(emails, post_data['email'])

        self.request('/api/user.json', method='PUT',
                     data=json.dumps(post_data), parser=lambda a: a)

        # update request.user
        me = self.get_profile()
        request.session.update({
            'profile': me,
            'username': me.get('username'),
            })
        request.session.changed()


def main(config):
    settings = config.registry.settings
    OpenstaxAccounts.server_url = settings['openstax_accounts.server_url']
    OpenstaxAccounts.application_id = settings['openstax_accounts.application_id']
    OpenstaxAccounts.application_secret = settings['openstax_accounts.application_secret']
    OpenstaxAccounts.application_url = settings['openstax_accounts.application_url']

    # Configure a message sending utility.
    msg_sending_util = {
        'default': send_message,
        'log': log_message,
        }[settings.get('openstax_accounts.message_sender', 'default')]
    config.registry.registerUtility(msg_sending_util, IMessageSender)

    openstax_accounts = OpenstaxAccounts()
    openstax_accounts.request_application_token()
    config.registry.registerUtility(openstax_accounts, IOpenstaxAccounts)

    config.registry.registerUtility(OpenstaxAccounts, IOpenstaxAccounts,
            name='factory')
