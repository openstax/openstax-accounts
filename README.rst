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

2. Download chrome driver (and chrome if you don't have it):
   ``wget 'http://chromedriver.storage.googleapis.com/2.9/chromedriver_linux64.zip'``

3. Unzip chrome driver: ``unzip chromedriver_linux64.zip``

4. Add chrome driver to $PATH: ``export PATH=$PATH:.``

5. Make sure the $DISPLAY is set, for example: ``export DISPLAY=:0`` or install ``xvfb``

6. ``./bin/python setup.py test`` or ``xvfb-run ./bin/python setup.py test``
