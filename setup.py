from setuptools import setup

setup(
        name='openstax-accounts-pyramid',
        version='0.1',
        description='An example pyramid app that connects to openstax/accounts',
        long_description=open('README.rst').read(),
        author='Karen Chan',
        author_email='karen@karen-chan.com',
        url='http://github.com/karenc/openstax-accounts-pyramid',
        install_requires=(
            'pyramid',
            'sanction',
            ),
        )
