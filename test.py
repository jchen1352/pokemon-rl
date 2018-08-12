import unittest
import logging
import time
from agents.base_agent import Agent
from sim import SimRunner

class TestAgent(Agent):
    def set_actions(self, actions):
        self.actions = actions
        self.action_num = 0

    def choose_action(self):
        action = self.actions[self.action_num]
        self.action_num += 1
        self.wait_game = True
        self.force_switch = False
        self.choose_start = False
        return action

class Test(unittest.TestCase):
    def setUp(self):
        self.agent1 = TestAgent('a')
        self.agent2 = TestAgent('b')
        self.sim_runner = SimRunner(self.agent1, self.agent2)

    def tearDown(self):
        self.sim_runner.clean_up()
        print('Done')

    def test_switches(self):
        print('Testing switches...')
        silent = True
        team1 = '|butterfree|||uturn|||||||]|jirachi|||wish|||||||'
        team2 = '|jirachi|||wish|||||||]|butterfree|||uturn|||||||'
        self.agent1.set_actions(['team 1', 'move 1', 'switch 2', 'switch 2'])
        self.agent2.set_actions(['team 2', 'switch 2', 'switch 2'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team1, team2)
        self.sim_runner.run_until_request(silent=silent)
        #p1 butterfree, p2 butterfree
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.name, 'butterfree')
        self.assertEqual(g1.active.moves[0].name, 'uturn')
        self.assertEqual(g1.team[1].name, 'jirachi')
        self.assertEqual(g1.team[1].moves[0].name, 'wish')
        #p1 uturn, p2 jirachi
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.opp_active.name, 'jirachi')
        #p1 jirachi
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.name, 'jirachi')
        self.assertEqual(g2.opp_active.name, 'jirachi')
        #p1 butterfree, p2 butterfree
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.moves[0].name, 'uturn')
        self.assertEqual(g2.opp_active.moves[0].name, 'uturn')
        self.assertEqual(g1.team[1].moves[0].name, 'wish')
        self.assertEqual(g2.active.moves[0].name, 'uturn')
        self.assertEqual(g2.team[1].moves[0].name, 'wish')

    def test_change(self):
        print('Testing form changes...')
        silent = True
        team1 = '|gyarados|gyaradosite|moxie|flamethrower|||||||'
        team2 = '|necrozmaduskmane|ultranecroziumz||photongeyser|||||||'
        self.agent1.set_actions(['team 1', 'move 1 mega'])
        self.agent2.set_actions(['team 1', 'move 1 ultra'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team1, team2)
        self.sim_runner.run_until_request(silent=silent)
        #p1 gyarados, p2 necrozmaduskmane
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.name, 'gyarados')
        self.assertEqual(g1.opp_active.name, 'necrozmaduskmane')
        self.assertEqual(g1.opp_active.ability, 'prismarmor')
        #p1 flamethrower mega, p2 photongeyser ultra
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.opp_active.name, 'necrozmaultra')
        self.assertEqual(g1.opp_active.ability, 'neuroforce')
        self.assertEqual(g2.opp_active.name, 'gyaradosmega')
        self.assertEqual(g2.opp_active.ability, 'moldbreaker')
        self.assertTrue(g1.mega)
        self.assertTrue(g2.opp_mega)

    def test_status(self):
        print('Testing status...')
        silent = True
        team1 = '|mew|chestoberry||healbell,rest,defog|||||||' + \
            ']|zygarde|||glare|||||||'
        team2 = '|toxapex|flameorb||toxic,toxicspikes|||||||' + \
            ']|clefable|||moonlight|||||||'
        self.agent1.set_actions(['team 1', 'move 3', 'move 3', 'switch 2',
            'move 1', 'switch 2', 'move 1', 'move 2'])
        self.agent2.set_actions(['team 1', 'move 1', 'move 2', 'switch 2',
            'move 1', 'move 1', 'move 1', 'move 1'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team1, team2)
        self.sim_runner.run_until_request(silent=silent)
        #p1 mew, p2 toxapex
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.opp_active.status, None)
        self.assertEqual(g2.opp_active.status, None)
        #p1 defog, p2 toxic
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.opp_active.status, 'brn')
        self.assertEqual(g1.opp_active.item, 'flameorb')
        self.assertEqual(g2.opp_active.status, 'tox')
        #p1 defog, p2 toxicspikes
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        #p1 zygarde, p2 clefable
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.opp_active.status, 'psn')
        #p1 glare, p2 moonlight
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.opp_active.status, 'par')
        #p1 mew, p2 moonlight
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        #p1 healbell, p2 moonlight
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.opp_active.status, None)
        self.assertEqual(g2.opp_team[1].name, 'zygarde')
        self.assertEqual(g2.opp_team[1].status, None)
        self.assertEqual(g2.opp_active.item, None)
        #p1 rest, p2 moonlight
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.opp_active.status, None)
        self.assertEqual(g2.opp_active.item, '') #Used chesto berry

    def test_boosts(self):
        print('Testing boosts...')
        silent = True
        team1 = '|cloyster|whiteherb|1|shellsmash|||||||]' + \
            '|primeape||1|closecombat|||||||]' + \
            '|malamar|||guardswap,topsyturvy|||||||'
        team2 = '|pangoro|||stormthrow|||||||]' + \
            '|marshadow|||spectralthief,bulkup|||||||]' + \
            '|drifblim|||clearsmog,haze,minimize|||||||'
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('anythinggoes', team1, team2)
        self.agent1.set_actions(['team 1', 'move 1', 'switch 2', 'move 1',
            'move 1', 'switch 3', 'move 1', 'move 2', 'move 1', 'move 1',
            'move 1', 'move 1', 'switch 2'])
        self.agent2.set_actions(['team 1', 'move 1', 'move 1', 'move 1',
            'switch 2', 'move 1', 'move 2', 'move 2', 'switch 3', 'move 3',
            'move 1', 'move 2', 'move 3'])
        self.sim_runner.run_until_request(silent=silent)
        #p1 cloyster, p2 pangoro
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        #p1 shellsmash, p2 stormthrow
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.boost_list(), [2,0,2,0,2,0,0])
        self.assertEqual(g2.opp_boost_list(), [2,0,2,0,2,0,0])
        #p1 primeape, p2 stormthrow
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.name, 'primeape')
        self.assertEqual(g1.boost_list(), [6,0,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [6,0,0,0,0,0,0])
        self.assertEqual(g2.opp_active.ability, 'angerpoint')
        #p1 closecombat, p2 stormthrow
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.boost_list(), [6,-1,0,-1,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [6,-1,0,-1,0,0,0])
        #p2 marshadow
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.active.name, 'marshadow')
        #p1 closecombat, p2 spectralthief
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.boost_list(), [6,0,0,0,0,0,0])
        self.assertEqual(g1.opp_boost_list(), [6,0,0,0,0,0,0])
        #p1 malamar
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.name, 'malamar')
        #p1 guardswap, p2 bulkup
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.boost_list(), [0,1,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [0,1,0,0,0,0,0])
        self.assertEqual(g2.boost_list(), [6,0,0,0,0,0,0])
        self.assertEqual(g1.opp_boost_list(), [6,0,0,0,0,0,0])
        #p1 topsyturvy, p2 bulkup
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.boost_list(), [0,1,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [0,1,0,0,0,0,0])
        self.assertEqual(g2.boost_list(), [-6,-1,0,0,0,0,0])
        self.assertEqual(g1.opp_boost_list(), [-6,-1,0,0,0,0,0])
        #p1 guardswap, p2 drifblim
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.active.name, 'drifblim')
        self.assertEqual(g1.boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g2.boost_list(), [0,1,0,0,0,0,0])
        self.assertEqual(g1.opp_boost_list(), [0,1,0,0,0,0,0])
        #p1 guardswap, p2 minimize
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.boost_list(), [0,1,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [0,1,0,0,0,0,0])
        self.assertEqual(g2.boost_list(), [0,0,0,0,0,0,2])
        self.assertEqual(g1.opp_boost_list(), [0,0,0,0,0,0,2])
        #p1 guardswap, p2 clearsmog
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g2.boost_list(), [0,0,0,0,0,0,2])
        self.assertEqual(g1.opp_boost_list(), [0,0,0,0,0,0,2])
        #p1 guardswap, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g2.boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g1.opp_boost_list(), [0,0,0,0,0,0,0])
        #p1 primeape, p2 minimize
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.name, 'cloyster')
        self.assertEqual(g1.boost_list(), [0,0,0,0,0,0,0])
        self.assertEqual(g2.opp_boost_list(), [0,0,0,0,0,0,0])

    def test_zmove1(self):
        print('Testing zmove1...')
        silent = True
        team1 = '|mew|mewniumz||psychic|||||||'
        team2 = '|jirachi|psychiumz||heartstamp|||||||'
        self.agent1.set_actions(['team 1', 'move 1 zmove'])
        self.agent2.set_actions(['team 1', 'move 1 zmove'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team1, team2)
        self.sim_runner.run_until_request(silent=silent)
        #p1 mew, p2 jirachi
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertFalse(g1.zmove)
        self.assertFalse(g2.opp_zmove)
        self.assertFalse(g2.zmove)
        self.assertFalse(g1.opp_zmove)
        #p1 genesissupernova, p2 shatteredpsyche
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertTrue(g1.zmove)
        self.assertTrue(g2.opp_zmove)
        self.assertTrue(g2.zmove)
        self.assertTrue(g1.opp_zmove)
        self.assertEqual(g2.opp_active.moves[0].name, 'psychic')
        self.assertEqual(g2.opp_active.item, 'mewniumz')
        self.assertEqual(g1.opp_active.item, 'psychiumz')

    def test_zmove2(self):
        print('Testing zmove2...')
        silent = True
        team1 = '|mew|mewniumz||psychic|||||||'
        team2 = '|jirachi|psychiumz||reflect|||||||'
        self.agent1.set_actions(['team 1', 'move 1'])
        self.agent2.set_actions(['team 1', 'move 1 zmove'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team1, team2)
        self.sim_runner.run_until_request(silent=silent)
        #p1 mew, p2 jirachi
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertFalse(g1.zmove)
        self.assertFalse(g2.opp_zmove)
        self.assertFalse(g2.zmove)
        self.assertFalse(g1.opp_zmove)
        #p1 genesissupernova, p2 shatteredpsyche
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertFalse(g1.zmove)
        self.assertFalse(g2.opp_zmove)
        self.assertTrue(g2.zmove)
        self.assertTrue(g1.opp_zmove)
        self.assertEqual(g1.opp_active.moves[0].name, 'reflect')
        self.assertEqual(g1.opp_active.item, 'psychiumz')

    def test_type_change(self):
        print('Testing type changes...')
        silent = True
        team1 = '|typhlosion|||burnup|||||||]' + \
            '|greninja||H|haze|||||||]' + \
            '|kecleon|||nastyplot|||||||]' + \
            '|smeargle|||forestscurse,reflecttype,conversion,soak|||||||'
        team2 = '|toxapex|||hiddenpowerice,haze|||||||'
        self.agent1.set_actions(['team 1', 'move 1', 'switch 2', 'move 1',
            'switch 3', 'switch 4', 'move 1', 'move 2', 'move 4'])
        self.agent2.set_actions(['team 1', 'move 2', 'move 2', 'move 2',
            'move 1', 'move 2', 'move 2', 'move 2', 'move 2'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team1, team2)
        self.sim_runner.run_until_request(silent=silent)
        #p1 typhlosion, p2 toxapex
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        #p1 burnup, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.types, [''])
        self.assertEqual(g2.opp_active.types, [''])
        #p1 greninja, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        #p1 haze, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.types, ['ice'])
        self.assertEqual(g2.opp_active.types, ['ice'])
        self.assertEqual(g2.opp_active.ability, 'protean')
        #p1 kecleon, p2 hiddenpowerice
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.types, ['ice'])
        self.assertEqual(g2.opp_active.types, ['ice'])
        self.assertEqual(g2.opp_active.ability, 'colorchange')
        #p1 smeargle, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        #p1 forestscurse, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.active.types, ['poison', 'water', 'grass'])
        self.assertEqual(g1.opp_active.types, ['poison', 'water', 'grass'])
        #p1 reflecttype, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.types, ['poison', 'water', 'grass'])
        self.assertEqual(g2.opp_active.types, ['poison', 'water', 'grass'])
        #p1 soak, p2 haze
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g2.active.types, ['water'])
        self.assertEqual(g1.opp_active.types, ['water'])

    def test_volatile_status(self):
        def check_effects(poke_effects, effects):
            for eff in poke_effects:
                if eff in effects:
                    self.assertTrue(poke_effects[eff])
                else:
                    self.assertFalse(poke_effects[eff])
        print('Testing volatile statuses...')
        silent = True
        team = '|wobbuffet|||counter,destinybond,encore,safeguard|||||||]' + \
            '|gengar|||curse,embargo,attract,disable|||||||]' + \
            '|celebi|||leechseed,healblock,telekinesis,solarbeam|||||||]' + \
            '|azumarill|||perishsong,substitute,aquaring|||||||]' + \
            '|darkrai|||nightmare,torment,swagger,taunt|||||||]' + \
            '|smeargle|||miracleeye,spore,ingrain,magnetrise|||||||'
        self.agent1.set_actions(['team 3', 'move 4', 'move 1', 'move 3',
            'move 1', 'switch 6'])
        self.agent2.set_actions(['team 4', 'move 2', 'move 1', 'move 3',
            'move 3', 'move 3'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team, team)
        self.sim_runner.run_until_request(silent=silent)
        #p1 celebi, p2 azumarill
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        #p1 solarbeam, p2 substitute
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        check_effects(g2.poke_effects, ['substitute'])
        check_effects(g1.opp_poke_effects, ['substitute'])
        #p1 solarbeam, p2 perishsong
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        check_effects(g1.poke_effects, ['perish3'])
        check_effects(g2.opp_poke_effects, ['perish3'])
        check_effects(g2.poke_effects, ['perish3'])
        check_effects(g1.opp_poke_effects, ['perish3'])
        #p1 telekinesis, p2 aquaring
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        check_effects(g1.poke_effects, ['perish3', 'perish2'])
        check_effects(g2.opp_poke_effects, ['perish3', 'perish2'])
        check_effects(g2.poke_effects, ['perish3', 'perish2', 'telekinesis',
            'aquaring'])
        check_effects(g1.opp_poke_effects, ['perish3', 'perish2', 'telekinesis',
            'aquaring'])
        #p1 leechseed, p2 aquaring
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        check_effects(g1.poke_effects, ['perish3', 'perish2', 'perish1'])
        check_effects(g2.opp_poke_effects, ['perish3', 'perish2', 'perish1'])
        check_effects(g2.poke_effects, ['perish3', 'perish2', 'perish1',
            'telekinesis', 'aquaring', 'leechseed'])
        check_effects(g1.opp_poke_effects, ['perish3', 'perish2', 'perish1',
            'telekinesis', 'aquaring', 'leechseed'])
        #p1 smeargle, p2 aquaring
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        check_effects(g1.poke_effects, [])
        check_effects(g2.opp_poke_effects, [])
        self.assertEqual(g2.active.status, 'fnt')

    def test_transform(self):
        print('Testing transform...')
        silent = True
        team1 = '|ditto||H|transform|||||||]|mew|||transform|||||||'
        team2 = '|porygonz||H|agility,conversion|||||||'
        self.agent1.set_actions(['team 1', 'switch 2', 'move 1', 'switch 2', 'switch 2'])
        self.agent2.set_actions(['team 1', 'move 1', 'move 2', 'move 2', 'move 2'])
        g1 = self.agent1.game_data
        g2 = self.agent2.game_data
        self.sim_runner.start('ubers', team1, team2)
        self.sim_runner.run_until_request(silent=silent)
        #p1 ditto, p2 porygonz
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertTrue(g1.active.transformed)
        self.assertEqual(g1.active.moves[0].name, 'agility')
        self.assertEqual(g1.active.moves[1].name, 'conversion')
        self.assertEqual(g1.opp_active.moves[0].name, 'agility')
        self.assertEqual(g1.opp_active.moves[1].name, 'conversion')
        self.assertEqual(g2.active.moves[0].name, 'agility')
        self.assertEqual(g2.active.moves[1].name, 'conversion')
        self.assertEqual(g2.opp_active.moves[0].name, 'agility')
        self.assertEqual(g2.opp_active.moves[1].name, 'conversion')
        self.assertEqual(g1.active.ability, 'analytic')
        self.assertEqual(g1.opp_active.ability, 'analytic')
        self.assertEqual(g1.active.types, ['normal'])
        self.assertEqual(g2.opp_active.ability, 'analytic')
        self.assertEqual(g2.opp_active.base_ability, 'imposter')
        #p1 mew, p2 agility
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.ability, 'synchronize')
        self.assertEqual(g2.opp_active.name, 'mew')
        self.assertEqual(g2.opp_active.ability, 'synchronize')
        #p1 transform, p2 conversion
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertTrue(g1.active.transformed)
        self.assertEqual(g1.boost_list(), [0,0,0,0,2,0,0])
        self.assertEqual(g1.active.types, ['psychic'])
        self.assertEqual(g1.active.ability, 'analytic')
        self.assertEqual(g2.opp_boost_list(), [0,0,0,0,2,0,0])
        self.assertEqual(g2.opp_active.types, ['psychic'])
        self.assertEqual(g2.opp_active.ability, 'analytic')
        self.assertEqual(g2.opp_active.moves[0].name, 'agility')
        self.assertEqual(g2.opp_active.moves[1].name, 'conversion')
        #p1 ditto, p2 conversion
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertEqual(g1.active.moves[0].name, 'agility')
        self.assertEqual(g1.active.moves[1].name, 'conversion')
        self.assertEqual(g1.opp_active.moves[0].name, 'agility')
        self.assertEqual(g1.opp_active.moves[1].name, 'conversion')
        self.assertEqual(g2.active.moves[0].name, 'agility')
        self.assertEqual(g2.active.moves[1].name, 'conversion')
        self.assertEqual(g2.opp_active.moves[0].name, 'agility')
        self.assertEqual(g2.opp_active.moves[1].name, 'conversion')
        self.assertEqual(g1.boost_list(), [0,0,0,0,2,0,0])
        self.assertEqual(g1.active.ability, 'analytic')
        self.assertEqual(g1.opp_active.ability, 'analytic')
        self.assertEqual(g1.active.types, ['psychic'])
        self.assertEqual(g2.opp_boost_list(), [0,0,0,0,2,0,0])
        self.assertEqual(g2.opp_active.types, ['psychic'])
        self.assertEqual(g2.opp_active.ability, 'analytic')
        self.assertEqual(g2.opp_active.base_ability, 'imposter')
        #p1 mew, p2 conversion
        self.sim_runner.run_actions(silent=silent)
        self.sim_runner.run_until_request(silent=silent)
        self.assertFalse(g1.active.transformed)
        self.assertEqual(g1.active.ability, 'synchronize')
        self.assertEqual(g2.opp_active.ability, 'synchronize')
        self.assertEqual(g2.opp_active.moves[0].name, 'transform')

if __name__ == '__main__':
    logging.basicConfig(filename='showdown.log', level=logging.INFO)
    unittest.main()
