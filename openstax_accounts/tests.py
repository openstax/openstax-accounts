try:
    import ConfigParser # python2
except ImportError:
    import configparser as ConfigParser # renamed in python3
import functools
import json
import os
import random
import subprocess
import time
import re
import unittest
try:
    import urlparse # python2
except ImportError:
    import urllib.parse as urlparse # renamed in python3

from pyramid.settings import asbool
from selenium import webdriver

def screenshot_on_error(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except:
            self.driver.get_screenshot_as_file('error.png')
            with open('error.html', 'w') as f:
                f.write(self.driver.page_source.encode('utf-8'))
            print(self.driver.page_source)
            raise
    return wrapper

def log(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        result = method(self, *args, **kwargs)
        return result
    return wrapper


class FunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testing_ini = os.getenv('TESTING_INI', 'testing.ini')

        cls.config = ConfigParser.ConfigParser({
            'openstax_accounts.stub': 'false',
            })
        cls.config.read([cls.testing_ini])
        cls.app_url = cls.config.get('app:main', 'openstax_accounts.application_url')

        if not asbool(cls.config.get('app:main', 'openstax_accounts.stub')):
            cls.set_up_accounts()

        # start server
        if os.path.exists('./bin/pserve'):
            pserve = './bin/pserve'
        else:
            pserve = 'pserve'
        cls.server = subprocess.Popen([pserve, cls.testing_ini])

        time.sleep(5)

    @classmethod
    @screenshot_on_error
    def set_up_accounts(cls):
        driver = os.getenv('DRIVER', 'Chrome')
        cls.driver = getattr(webdriver, driver)()

        cls.accounts_url = cls.config.get('app:main', 'openstax_accounts.server_url')

        admin_login = cls.config.get('app:main', 'openstax_accounts.admin_login')
        admin_password = cls.config.get('app:main', 'openstax_accounts.admin_password')

        # login as admin in openstax/accounts
        cls.driver.get(urlparse.urljoin(cls.accounts_url, '/login'))
        cls.class_fill_in('Username', admin_login)
        cls.class_fill_in('Password', admin_password)
        cls.driver.find_element_by_xpath('//button[text()="Sign in"]').click()
        time.sleep(5)

        # register our app with openstax/accounts
        cls.driver.get(urlparse.urljoin(cls.accounts_url, '/oauth/applications'))
        cls.driver.find_element_by_link_text('New Application').click()
        cls.class_fill_in('Name', 'pyramid')
        cls.class_fill_in('Redirect uri', urlparse.urljoin(cls.app_url, '/callback'))
        cls.class_fill_in('Email subject prefix', '[pyramid]')
        cls.class_fill_in('Email from address', 'pyramid@e-mail-tester.appspotmail.com')
        cls.driver.find_element_by_id('application_trusted').click()
        cls.driver.find_element_by_name('commit').click()
        time.sleep(5)
        application_id = cls.driver.find_element_by_id('application_id').text
        application_secret = cls.driver.find_element_by_id('secret').text
        cls.driver.quit()

        cls.config.set('app:main', 'openstax_accounts.application_id',
                application_id)
        cls.config.set('app:main', 'openstax_accounts.application_secret',
                application_secret)

        with open(cls.testing_ini, 'w') as f:
            cls.config.write(f)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()

    def fill_in(self, label_text, value):
        for i in range(10):
            # try this 10 times to minimize false negative results...
            try:
                label = self.driver.find_element_by_xpath('//label[text()="{}"]'
                        .format(label_text))
                break
            except:
                time.sleep(5)
                if i == 9:
                    raise

        input_id = label.get_attribute('for')
        field = self.driver.find_element_by_id(input_id)
        field.send_keys(value)

    class_fill_in = classmethod(fill_in)

    def setUp(self):
        driver = os.getenv('DRIVER', 'Chrome')
        self.driver = getattr(webdriver, driver)()

    def tearDown(self):
        self.driver.quit()

    def follow_link(self, link_text, exact=True):
        if exact:
            self.driver.find_element_by_link_text(link_text).click()
        else:
            self.driver.find_element_by_partial_link_text(link_text).click()
        time.sleep(5)

    def generate_username(self, prefix='user'):
        length = 5
        n = '{:0>5d}'.format(random.randint(0, 10 ** length))
        return '{}_{}'.format(prefix, n)

    def page_text(self):
        return re.sub('<[^>]*>', '', self.driver.page_source)

    @screenshot_on_error
    def test_stub(self):
        # check that we are not logged in
        self.driver.get(self.app_url)
        self.assertTrue('You are currently not logged in' in self.driver.page_source)
        self.follow_link('Log in')
        # stub login form
        self.fill_in('Username:', 'test')
        self.fill_in('Password:', 'password')
        self.driver.find_element_by_xpath('//input[@type="submit"]').click()
        self.assertTrue('Username or password incorrect' in self.page_text())

        self.fill_in('Username:', 'aaron')
        self.fill_in('Password:', 'password')
        self.driver.find_element_by_xpath('//input[@type="submit"]').click()
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: aaron' in self.page_text())
        self.assertTrue('last_name: Andersen' in self.page_text())
        # logout
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

        # login as someone else
        self.follow_link('Log in')
        self.fill_in('Username:', 'babara')
        self.fill_in('Password:', 'password')
        self.driver.find_element_by_xpath('//input[@type="submit"]').click()
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: babara' in self.page_text())
        # check user search api
        self.follow_link('User Search (JSON)')
        users = json.loads(self.page_text())
        self.assertEqual(users['total_count'], 6)
        # users sorted by first name and last name
        self.assertEqual(
            sorted(users['items'],
                   lambda a, b: cmp(a['username'], b['username'])),
            [{'username': 'aaron', 'id': 1,
              'first_name': "Aaron", 'last_name': "Andersen"},
             {'username': 'babara', 'id': 2},
             {'username': 'caitlin', 'id': 3,
              'first_name': 'Test', 'last_name': 'User', 'title': None,
              'full_name': 'Test User'},
             {'username': 'dale', 'id': 4,
              'first_name': 'Test', 'last_name': 'User', 'title': None,
              'full_name': 'Test User'},
             {'username': 'earl', 'id': 5,
              'first_name': 'Test', 'last_name': 'User', 'title': None,
              'full_name': 'Test User'},
             {'username': 'fabian', 'id': 6,
              'first_name': 'Test', 'last_name': 'User', 'title': None,
              'full_name': 'Test User'},
             ])
        # check messaging api
        self.driver.get(self.app_url)
        self.follow_link('Send Message')
        self.fill_in('Username:', 'earl')
        self.fill_in('Subject:', 'Test')
        self.fill_in('Body:', 'Dear Earl,\n\nMessage!')
        self.driver.find_elements_by_xpath('//input')[-1].click()
        time.sleep(5)
        self.assertTrue('Message sent' in self.page_text())
        # check messages.txt
        with open('messages.txt', 'r') as f:
            # Note, on multiple tests runs this can have more than one
            # message inside the file.
            messages = f.read()
        # Parse out the messages using the message delimiter.
        messages = [x for x in messages.split('\n\n\n') if x.strip()]
        # Grab the last message.
        message = json.loads(messages[-1])
        expected = {
            u'body[html]': u'<html><body>Dear Earl,\r\n<br/>\r\n<br/>Message!</body></html>',
            u'body[text]': u'Dear Earl,\r\n\r\nMessage!',
            u'subject': u'Test',
            u'to[user_ids][]': [5],
 u'user_id': 5}
        self.assertEqual(message, expected)
        # logout
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

    @screenshot_on_error
    def test_local(self):
        self._test_signup()
        self._test_login()
        self._test_search()
        self._test_edit_profile()

    def _test_edit_profile(self):
        # login
        self.driver.get(self.app_url)
        self.follow_link('Log in')
        # redirected to openstax accounts
        self.fill_in('Username', self.username)
        self.fill_in('Password', 'password')
        self.driver.find_element_by_xpath('//button[text()="Sign in"]').click()
        time.sleep(5)
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(self.username)
                        in self.page_text())
        # update profile data
        self.fill_in('First Name:', 'Test')
        self.fill_in('Last Name:', 'User')
        self.driver.find_element_by_name('submit').click()

        # check updated profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(self.username)
                        in self.page_text())
        self.assertTrue('first_name: Test' in self.page_text())
        self.assertTrue('last_name: User' in self.page_text())

        # logout
        self.driver.get(self.app_url)
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

    def _test_signup(self):
        # check that we are not logged in
        self.driver.get(self.app_url)
        self.assertTrue('You are currently not logged in' in self.driver.page_source)
        self.follow_link('Log in')
        # redirected to openstax accounts
        self.follow_link('Sign up')
        # fill out sign up form
        self.username = self.generate_username()
        self.fill_in('Username', self.username)
        self.fill_in('Password', 'password')
        self.fill_in('Password Again', 'password')
        self.driver.find_element_by_name('commit').click()
        # signed in to openstax accounts
        self.assertTrue('Nice to meet you' in self.page_text())
        self.follow_link('Finish setting up my account')
        # profile form
        if 'Complete your profile' in self.page_text():
            self.driver.find_element_by_id('register_i_agree').click()
            self.driver.find_element_by_id('register_submit').click()
        time.sleep(5)
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(self.username) in self.page_text())
        self.assertTrue('id: ' in self.page_text())
        # logout
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

    def _test_login(self):
        # check that we are not logged in
        self.driver.get(self.app_url)
        self.assertTrue('You are currently not logged in' in self.page_text())
        self.follow_link('Log in')
        # redirected to openstax accounts
        self.fill_in('Username', self.username)
        self.fill_in('Password', 'password')
        self.driver.find_element_by_xpath('//button[text()="Sign in"]').click()
        time.sleep(5)
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(self.username) in self.page_text())
        self.assertTrue('id: ' in self.page_text())
        # logout
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

    def _test_search(self):
        # login
        self.driver.get(self.app_url)
        self.follow_link('Log in')
        # redirected to openstax accounts
        self.fill_in('Username', self.username)
        self.fill_in('Password', 'password')
        self.driver.find_element_by_xpath('//button[text()="Sign in"]').click()
        time.sleep(5)
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        self.follow_link('User Search (JSON)')
        for i in range(10):
            try:
                users = json.loads(self.page_text())
                break
            except:
                if i == 9:
                    raise
        self.assertEqual(users['total_count'], 1)
        self.assertEqual(len(users['items']), 1)
        self.assertEqual(users['items'][0]['username'], self.username)

        # logout
        self.driver.get(self.app_url)
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

    @screenshot_on_error
    def test_facebook(self):
        facebook = dict(self.config.items('test:facebook'))
        # check that we are not logged in
        self.driver.get(self.app_url)
        self.assertTrue('You are currently not logged in' in self.page_text())
        self.follow_link('Log in')
        # redirected to openstax accounts
        self.driver.find_element_by_xpath(
                '//img[@title="Sign in using your Facebook account"]').click()
        # redirected to facebook
        self.fill_in('Email or Phone:', facebook['login'])
        self.fill_in('Password:', facebook['password'])
        self.driver.find_element_by_name('login').click()
        confirm = self.driver.find_elements_by_name('__CONFIRM__')
        if confirm:
            confirm[0].click()
            time.sleep(5)
        # redirected back to openstax accounts
        if 'Nice to meet you' in self.page_text():
            self.follow_link('Finish setting up my account')
        # profile form
        if 'Complete your profile' in self.page_text():
            self.driver.find_element_by_id('register_i_agree').click()
            self.driver.find_element_by_id('register_submit').click()
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(facebook['username']) in self.page_text())
        self.assertTrue('id: ' in self.page_text())
        # logout
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

    @screenshot_on_error
    def test_twitter(self):
        twitter = dict(self.config.items('test:twitter'))
        # check that we are not logged in
        self.driver.get(self.app_url)
        self.assertTrue('You are currently not logged in' in self.page_text())
        self.follow_link('Log in')
        # redirected to openstax accounts
        self.driver.find_element_by_xpath(
                '//img[@title="Sign in using your Twitter account"]').click()
        # redirected to twitter
        login = self.driver.find_element_by_id('username_or_email')
        login.send_keys(twitter['login'])
        password = self.driver.find_element_by_id('password')
        password.send_keys(twitter['password'])
        self.driver.find_element_by_id('allow').click()
        time.sleep(5)
        # redirected back to openstax accounts
        if 'Nice to meet you' in self.page_text():
            self.follow_link('Finish setting up my account')
        # profile form
        if 'Complete your profile' in self.page_text():
            self.driver.find_element_by_id('register_i_agree').click()
            self.driver.find_element_by_id('register_submit').click()
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(twitter['username']) in self.page_text())
        self.assertTrue('id: ' in self.page_text())
        # logout
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())

    @screenshot_on_error
    def test_google(self):
        google = dict(self.config.items('test:google'))
        # check that we are not logged in
        self.driver.get(self.app_url)
        self.assertTrue('You are currently not logged in' in self.page_text())
        self.follow_link('Log in')
        # redirected to openstax accounts
        self.driver.find_element_by_xpath(
                '//img[@title="Sign in using your Google account"]').click()
        # redirected to google
        login = self.driver.find_element_by_id('Email')
        login.send_keys(google['login'])
        password = self.driver.find_element_by_id('Passwd')
        password.send_keys(google['password'])
        self.driver.find_element_by_id('signIn').click()
        time.sleep(5)
        # redirected back to openstax accounts
        if 'Nice to meet you' in self.page_text():
            self.follow_link('Finish setting up my account')
        # profile form
        if 'Complete your profile' in self.page_text():
            self.driver.find_element_by_id('register_i_agree').click()
            self.driver.find_element_by_id('register_submit').click()
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(google['username']) in self.page_text())
        self.assertTrue('id: ' in self.page_text())
        # logout
        self.follow_link('Log out')
        self.assertTrue('You are currently not logged in' in self.page_text())
