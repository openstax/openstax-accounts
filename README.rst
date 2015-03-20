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

1. Copy testing.ini to local_testing.ini and change the values.
   This is only necessary if you intent to run the functional tests against
   a local instance of openstax/accounts.
   ::

     cp testing.ini.example local_testing.ini

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

6. Run tests without openstax/accounts ::

     xvfb-run ./bin/python setup.py test

   or to run all tests (include the ``LOCAL_INI``,
   which requires an openstax/accounts install)::

     LOCAL_INI=local_testing.ini xvfb-run ./bin/python setup.py test
