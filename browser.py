import logging
import time
import re
import json
import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, \
    NoSuchElementException, StaleElementReferenceException
from pokemon import Move, Pokemon
from agents.base_agent import Agent

class Browser():
    def __init__(self, agent, human_control=False):
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.StreamHandler())
        self.agent = agent
        self.human_control = human_control
    
    def start_driver(self, timeout=10):
        self.logger.info('Starting driver')
        #Enable reading of Chrome console log
        d = DesiredCapabilities.CHROME
        d['loggingPrefs'] = { 'browser':'ALL' }
        #Start maximized
        o = webdriver.ChromeOptions()
        o.add_argument('--start-maximized')
        self.driver = webdriver.Chrome(chrome_options=o, desired_capabilities=d)
        self.driver.get('https://play.pokemonshowdown.com/')
        #Play on local server
        self.driver.get('http://localhost.psim.us/')
        self.timeout = timeout
        self.driver.implicitly_wait(timeout)
        self.console_stream = self.create_console_stream()

    def mute_sound(self):
        try:
            self.driver.find_element_by_css_selector(".icon[name='openSounds']").click()
        except StaleElementReferenceException:
            self.driver.find_element_by_css_selector(".icon[name='openSounds']").click()
        self.driver.find_element_by_css_selector("[name='muted']").click()

    def login(self, username, password):
        self.logger.info('Logging in')
        self.driver.find_element_by_name('login').click()
        user = self.driver.find_element_by_name('username')
        user.send_keys(username)
        user.send_keys(Keys.RETURN)
        passwd = self.driver.find_element_by_name('password')
        passwd.send_keys(password)
        passwd.send_keys(Keys.RETURN)

    def challenge(self, username):
        self.logger.info('Challenging %s', username)
        self.driver.find_element_by_name('finduser').click()
        user = self.driver.find_element_by_name('data')
        user.send_keys(username)
        user.send_keys(Keys.RETURN)
        try:
            self.driver.find_element_by_name('challenge').click()
        except NoSuchElementException:
            self.logger.info('User %s is not online', username)
            return
        #Sometimes tries to click on button on previous page, try again
        except StaleElementReferenceException:
            self.driver.find_element_by_name('challenge').click()
        self.driver.find_element_by_name('makeChallenge').click()
        #Wait until challenge accepted
        url = self.driver.current_url
        while (url == self.driver.current_url):
            time.sleep(2)
        self.game_loop()

    def game_loop(self):
        while True:
            time.sleep(2)
            self.process_stream()
            if not self.agent.wait_game:
                self.logger.info('Active: {}'.format(self.agent.game_data.active))
                self.logger.info('Opp: {}'.format(self.agent.game_data.opp_active))
                choice = self.agent.choose_action()
                if not self.human_control:
                    self.make_choice(choice)

    def make_choice(self, choice):
        self.logger.info('Choosing %s', choice)
        m = re.match('(move|switch) (\d)', choice)
        css = '.{}menu button'.format(m.group(1))
        try:
            buttons = WebDriverWait(self.driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, css)))
            buttons[int(m.group(2))-1].click()
            self.wait_game = True
            self.force_switch = False
        except TimeoutException:
            self.logger.warning('Could not find buttons to click')

    #Creates a generator that yields every console log line sequentially,
    #or yields None if there are currently no further messages
    def create_console_stream(self):
        while True:
            log = self.driver.get_log('browser')
            if len(log) > 0:
                for entry in log:
                    m = re.match('[^|]*(\|.*)"', entry['message'])
                    if m:
                        #Browser output has extra backslashes
                        message = m.group(1).replace('\\n', '\n').replace('\\', '')
                        for line in message.splitlines():
                            yield line
            else:
                yield None

    def flush_console_stream(self):
        while (next(self.console_stream)):
            pass

    def process_stream(self):
        message = next(self.console_stream)
        request = ''
        while message:
            self.logger.info(message)
            self.agent.process_message(message)
            message = next(self.console_stream)

if __name__ == '__main__':
    logging.basicConfig(filename='showdown.log', level=logging.INFO)
    #Either put username and password in json file named 'login.json',
    #or pass in username and password as command line arguments
    #TODO: helpful help message
    try:
        with open('login.json') as f:
            login = json.load(f)
            username = login['username']
            password = login['password']
    except FileNotFoundError:
        parser = argparse.ArgumentParser()
        parser.add_argument('username')
        parser.add_argument('password')
        args = parser.parse_args()
        username = args.username
        password = args.password
    a = Agent(username)
    s = Browser(a, False)
    s.start_driver()
    s.mute_sound()
    s.login(username, password)
    s.flush_console_stream()
    s.challenge('deltaepsilon3')
