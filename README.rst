openstax-accounts-in-pyramid
============================

This is an example python pyramid app that connects to openstax/accounts.

INSTALL
-------

0. Install ``virtualenv``

1. ``virtualenv .``

2. ``./bin/python setup.py install``

3. Set up openstax/services (See karenc/openstax-setup)

4. Register this app with openstax/accounts

5. Copy development.ini.example to development.ini and change the values

6. Start the app by ``./bin/pserve development.ini``

TESTS
-----

1. Copy testing.ini.example to testing.ini and change the values

2. Download chrome driver::

     wget 'http://chromedriver.storage.googleapis.com/2.14/chromedriver_linux64.zip

   If you don't have chrome::

     sudo apt-get install chromium-browser

3. Unzip chrome driver::

     unzip chromedriver_linux64.zip

4. Add chrome driver to ``$PATH``::

     export PATH=$PATH:.

5. Make sure the ``$DISPLAY`` is set, for example::

     export DISPLAY=localhost:10.0

   or install ``xvfb``

6. Run browser tests with openstax/accounts::

     ./bin/python setup.py test -s openstax_accounts.tests.FunctionalTests

   or::

     xvfb-run ./bin/python setup.py test -s openstax_accounts.tests.FunctionalTests

7. Run stub tests without openstax/accounts::

     TESTING_INI=test_stub.ini ./bin/python setup.py test -s openstax_accounts.tests.StubTests

   or::

     TESTING_INI=test_stub.ini xvfb-run ./bin/python setup.py test -s openstax_accounts.tests.StubTests
