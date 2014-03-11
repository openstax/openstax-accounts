from setuptools import setup

setup(
        name='openstax-accounts-pyramid',
        version='0.1',
        description='An example pyramid app that connects to openstax/accounts',
        long_description=open('README.rst').read(),
        author='Karen Chan',
        author_email='karen@karen-chan.com',
        url='http://github.com/karenc/openstax-accounts-pyramid',
        packages=['openstax_accounts_pyramid'],
        install_requires=(
            'PasteDeploy',
            'pyramid',
            'sanction',
            'waitress',
            ),
        tests_require=(
            'selenium',
            ),
        test_suite='openstax_accounts_pyramid.tests',
        entry_points={
            'paste.app_factory': [
                'main = openstax_accounts_pyramid.example:main',
                ],
            },
        )
