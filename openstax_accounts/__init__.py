# -*- coding: utf-8 -*-

from pyramid.settings import asbool

def main(config):
    settings = config.registry.settings

    if asbool(settings.get('openstax_accounts.stub')):
        # use the stub authentication policy
        config.include('openstax_accounts.stub.main')
    else:
        # use the openstax accounts authentication policy
        config.include('openstax_accounts.openstax_accounts.main')
        config.include('openstax_accounts.authentication_policy.main')
