# -*- coding: utf-8 -*-
# ###
# Copyright (c) 2013, Rice University
# This software is subject to the provisions of the GNU Affero General
# Public License version 3 (AGPLv3).
# See LICENCE.txt for details.
# ###
from .openstax_accounts import OpenstaxAccounts


def includeme(config):
    """Initialize the package for use."""
    server_url = settings['openstax_accounts.server_url']
    application_id = settings['openstax_accounts.application_id']
    application_secret = settings['openstax_accounts.application_secret']
    application_url = settings['openstax_accounts.application_url']

    args = (server_url, application_id, application_secret, application_url)

    openstax_accounts = OpenstaxAccounts(*args)
    openstax_accounts.request_application_token()
    config.registry.registerUtility(openstax_accounts, IOpenstaxAccounts)
