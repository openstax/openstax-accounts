from setuptools import setup

setup(
        name='openstax-accounts',
        version='0.14.0',
        description='An example pyramid app that connects to openstax/accounts',
        long_description=open('README.rst').read(),
        author='Connexions team',
        author_email='info@cnx.org',
        url='http://github.com/Connexions/openstax-accounts',
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
