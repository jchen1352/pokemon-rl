import sys
import logging
import argparse
import os
import threading
import subprocess
import time
from agents.base_agent import Agent

class SimRunner:
    def __init__(self, agent1, agent2):
        self.agent1 = agent1
        self.agent2 = agent2

        if not os.path.exists('sim_in'):
            os.mkfifo('sim_in')
        if not os.path.exists('sim_out'):
            os.mkfifo('sim_out')
        t1 = threading.Thread(target=self._open_sim_pipes)
        t2 = threading.Thread(target=self.open_pipes)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.sim = subprocess.Popen(
            ['./Pokemon-Showdown/pokemon-showdown', 'simulate-battle'],
            stdin=self._sim_in,
            stdout=self._sim_out
        )
        self.logger = logging.getLogger(__name__)
        if len(self.logger.handlers) == 0:
            self.logger.addHandler(logging.StreamHandler())
        self.game_end = False

    def _open_sim_pipes(self):
        """Opens pipes for internal simulator to use"""
        self._sim_in = open('sim_in', 'r')
        self._sim_out = open('sim_out', 'w')

    def open_pipes(self):
        """Opens pipes to read from and write to simulator"""
        self.sim_in = open('sim_in', 'w')
        #Need non-blocking pipe
        self.sim_out = os.fdopen(os.open('sim_out', os.O_RDONLY | os.O_NONBLOCK))

    def write_sim(self, message):
        self.sim_in.write(message + '\n')
        self.sim_in.flush()

    def read_sim(self):
        #If sim_out is empty, message will be the empty string
        message = self.sim_out.readline()
        #Wait a little if empty to make sure it really is empty
        if message == '':
            time.sleep(.01)
            message = self.sim_out.readline()
        return message

    def start(self, game_format='random', p1team=None, p2team=None):
        if game_format == 'random':
            self.write_sim('>start {"formatid":"gen7randombattle"}')
            self.write_sim('>player p1 {"name":"%s"}' % self.agent1.player_name)
            self.write_sim('>player p2 {"name":"%s"}' % self.agent2.player_name)
        else:
            if p1team == None or p2team == None:
                self.logger.error('Missing teams')
                return
            self.write_sim('>start {"formatid":"gen7%s"}' % game_format)
            self.write_sim('>player p1 {"name":"%s", "team":"%s"}'
                % (self.agent1.player_name, p1team))
            self.write_sim('>player p2 {"name":"%s", "team":"%s"}'
                % (self.agent2.player_name, p2team))

    def run_until_request(self, silent=True):
        #Wait until sim_out has a message
        message = self.read_sim()
        while message == '':
            time.sleep(.01)
            message = self.read_sim()
        mode = 'both'
        #Read until sim_out has no more messages
        while message != '':
            message = message.strip()
            if not silent:
                self.logger.info(message)
            if message == 'end':
                self.game_end = True
            if mode == 'both':
                if message == 'sideupdate':
                    mode = 'sideupdate'
                elif message == '|split':
                    mode = 'splitspectator'
                else:
                    self.agent1.process_message(message)
                    self.agent2.process_message(message)
            elif mode == 'sideupdate':
                mode = 'sideupdate' + message
            elif mode == 'sideupdatep1':
                self.agent1.process_message(message)
                mode = 'both'
            elif mode == 'sideupdatep2':
                self.agent2.process_message(message)
                mode = 'both'
            elif mode == 'splitspectator':
                mode = 'splitp1'
            elif mode == 'splitp1':
                self.agent1.process_message(message)
                mode = 'splitp2'
            elif mode == 'splitp2':
                self.agent2.process_message(message)
                mode = 'splitomniscient'
            elif mode == 'splitomniscient':
                mode = 'both'
            else:
                #Unexpected, shouldn't be here
                mode = 'both'
            message = self.read_sim()

    def run_actions(self, silent=True):
        if not self.agent1.wait_game:
            choice1 = self.agent1.choose_action()
            s = '>p{} {}'.format(self.agent1.player_num, choice1)
            self.write_sim(s)
            if not silent:
                self.logger.info(s)
        if not self.agent2.wait_game:
            choice2 = self.agent2.choose_action()
            s = '>p{} {}'.format(self.agent2.player_num, choice2)
            self.write_sim(s)
            if not silent:
                self.logger.info(s)

    def run_game(self, game_format='random', silent=True):
        self.game_end = False
        self.start(game_format=game_format)
        while not self.game_end:
            self.run_until_request(silent=silent)
            self.run_actions(silent=silent)

    def clean_up(self):
        self.sim.terminate()
        self.sim.wait()
        self._sim_in.close()
        self._sim_out.close()
        self.sim_in.close()
        self.sim_out.close()

if __name__ == '__main__':
    logging.basicConfig(filename='showdown.log', level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('p1name', help='Player 1 name')
    parser.add_argument('p2name', help='Player 2 name')
    args = parser.parse_args()
    agent1 = Agent(args.p1name)
    agent2 = Agent(args.p2name)
    sim_runner = SimRunner(agent1, agent2)
    sim_runner.run_game(silent=False)
    sim_runner.clean_up()
