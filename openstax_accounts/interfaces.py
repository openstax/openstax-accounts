from zope.interface import Interface

class IOpenstaxAccounts(Interface):
    pass


class IOpenstaxAccountsAuthenticationPolicy(Interface):
    pass


class IMessageSender(Interface):
    """Utility for sending messages"""

    def __call__(msg_data):
        """Send the message using the given ``msg_data``."""
