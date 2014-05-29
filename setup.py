from setuptools import setup

setup(
        name='openstax-accounts',
        version='0.6',
        description='An example pyramid app that connects to openstax/accounts',
        long_description=open('README.rst').read(),
        author='Karen Chan',
        author_email='karen@karen-chan.com',
        url='http://github.com/karenc/openstax-accounts',
        license='LGPL',
        packages=['openstax_accounts'],
        install_requires=(
            'PasteDeploy',
            'pyramid',
            'sanction',
            'waitress',
            ),
        tests_require=(
            'selenium',
            ),
        test_suite='openstax_accounts.tests',
        entry_points={
            'paste.app_factory': [
                'main = openstax_accounts.example:main',
                ],
            },
        zip_safe=False,
        )
