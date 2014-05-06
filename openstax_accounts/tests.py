try:
    import ConfigParser # python2
except ImportError:
    import configparser as ConfigParser # renamed in python3
import functools
import os
import random
import subprocess
import re
import unittest
try:
    import urlparse # python2
except ImportError:
    import urllib.parse as urlparse # renamed in python3

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
        cls.driver = webdriver.Chrome()

        cls.testing_ini = os.getenv('TESTING_INI', 'testing.ini')

        cls.config = ConfigParser.ConfigParser()
        cls.config.read([cls.testing_ini])

        cls.app_url = cls.config.get('app:main', 'openstax_accounts.application_url')
        cls.accounts_url = cls.config.get('app:main', 'openstax_accounts.server_url')

        admin_login = cls.config.get('app:main', 'openstax_accounts.admin_login')
        admin_password = cls.config.get('app:main', 'openstax_accounts.admin_password')

        # login as admin in openstax/accounts
        cls.driver.get(urlparse.urljoin(cls.accounts_url, '/login'))
        cls.class_fill_in('Username', admin_login)
        cls.class_fill_in('Password', admin_password)
        cls.driver.find_element_by_xpath('//button[text()="Sign in"]').click()
        # register our app with openstax/accounts
        cls.driver.get(urlparse.urljoin(cls.accounts_url, '/oauth/applications'))
        cls.driver.find_element_by_link_text('New Application').click()
        cls.class_fill_in('Name', 'pyramid')
        cls.class_fill_in('Redirect uri', urlparse.urljoin(cls.app_url, '/callback'))
        cls.driver.find_element_by_id('application_trusted').click()
        cls.driver.find_element_by_name('commit').click()
        application_id = cls.driver.find_element_by_id('application_id').text
        application_secret = cls.driver.find_element_by_id('secret').text
        cls.driver.quit()

        cls.config.set('app:main', 'openstax_accounts.application_id',
                application_id)
        cls.config.set('app:main', 'openstax_accounts.application_secret',
                application_secret)

        with open(cls.testing_ini, 'w') as f:
            cls.config.write(f)

        # start server
        cls.server = subprocess.Popen(['./bin/pserve', cls.testing_ini])

        import time
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()

    def fill_in(self, label_text, value):
        label = self.driver.find_element_by_xpath('//label[text()="{}"]'
                .format(label_text))
        input_id = label.get_attribute('for')
        field = self.driver.find_element_by_id(input_id)
        field.send_keys(value)

    class_fill_in = classmethod(fill_in)

    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()

    def follow_link(self, link_text, exact=True):
        if exact:
            self.driver.find_element_by_link_text(link_text).click()
        else:
            self.driver.find_element_by_partial_link_text(link_text).click()

    def generate_username(self, prefix='user'):
        length = 5
        n = '{:0>5d}'.format(random.randint(0, 10 ** length))
        return '{}_{}'.format(prefix, n)

    def page_text(self):
        return re.sub('<[^>]*>', '', self.driver.page_source)

    @screenshot_on_error
    def test_local(self):
        self._test_signup()
        self._test_login()

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
        # redirected back to app
        self.assertTrue('You are currently logged in.' in self.page_text())
        # check profile data
        self.follow_link('Profile')
        self.assertTrue('username: {}'.format(self.username) in self.page_text())
        self.assertTrue('id: ' in self.page_text())
        # logout
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
