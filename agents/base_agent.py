import random
import logging
import json
import re
import numpy as np
from pokemon import Pokemon, Move, GameData
from dex import *

def parse_pokemon(s):
    """Get player num and pokemon nickname"""
    m = re.match('p(1|2)a: (.*)', s)
    return m.group(1), m.group(2)

class Agent:
    def __init__(self, player_name):
        self.player_name = player_name
        self.game_data = GameData()
        self.init_battle()
        self.logger = logging.getLogger(__name__)
        if len(self.logger.handlers) == 0:
            self.logger.addHandler(logging.StreamHandler())
        self.poke_to_ix = {poke:i for i, poke in enumerate(pokedex)}
        self.move_to_ix = {move:i for i, move in enumerate(movedex)}
        #Assign index 0 to having no item
        self.item_to_ix = {item:i+1 for i, item in enumerate(itemdex)}
        self.item_to_ix[''] = 0
        abilities = set()
        for p in pokedex:
            for a in pokedex[p]['abilities']:
                abilities.add(clean_name(a))
        #Assign index 0 to having no ability
        self.ability_to_ix = {a:i+1 for i, a in enumerate(abilities)}
        self.ability_to_ix[''] = 0
        self.types = {'bug': 0, 'dark': 1, 'dragon': 2, 'electric': 3,
            'fairy': 4, 'fighting': 5, 'fire': 6, 'flying': 7, 'ghost': 8,
            'grass': 9, 'ground': 10, 'ice': 11, 'normal': 12, 'poison': 13,
            'psychic': 14, 'rock': 15, 'steel': 16, 'water': 17}
        self.move_categories = {'physical': 0, 'special': 1, 'status': 2}
        self.move_targets = {'normal': 0, 'self': 1, 'all': 2, 'foeSide': 3,
            'adjacentAlly': 4, 'allySide': 5, 'allyTeam': 6}
        self.poke_statuses = {'brn': 0, 'frz': 1, 'par': 2, 'psn': 3, 'tox': 4,
            'slp': 5, 'fnt': 6}

    def init_battle(self):
        self.player_num = None
        self.wait_game = True
        self.force_switch = False
        self.choose_start = False
        self.game_data.reset()

    def choose_action(self):
        if self.wait_game:
            return None
        choice = ''
        if self.choose_start:
            choice = 'team 1'
        elif self.force_switch:
            #Choose a random pokemon to switch to
            possible = [i+1 for (i,p) in enumerate(self.game_data.team)
                if p != self.game_data.active and p.status != 'fnt']
            choice = 'switch ' + str(random.choice(possible))
        else:
            #Choose a random move from active pokemon
            p = self.game_data.active
            possible = [i+1 for (i,m) in enumerate(p.moves) if not m.disabled]
            choice = 'move ' + str(random.choice(possible))
        self.wait_game = True
        self.force_switch = False
        self.choose_start = False
        return choice

    def process_message(self, message):
        if message != '':
            args = message.split('|')
            if args[0] == '':
                kwargs = {}
                for i in range(len(args)-1, -1, -1):
                    m = re.match('\[([a-z]*)\] (.*)', args[i])
                    if m:
                        kwargs[m.group(1)] = m.group(2)
                        args.pop(i)
                self.process_args(args, kwargs)

    def other_player(self):
        if self.player_num == '1':
            return '2'
        return '1'

    def get_active(self, player):
        if player == self.player_num:
            return self.game_data.active
        return self.game_data.opp_active

    def get_boosts(self, player):
        if player == self.player_num:
            return self.game_data.boosts
        return self.game_data.opp_boosts

    def clear_boosts(self, player):
        b = self.game_data.boosts
        if player != self.player_num:
            b = self.game_data.opp_boosts
        for stat in b:
            b[stat] = 0

    def get_poke_effects(self, player):
        if player == self.player_num:
            return self.game_data.poke_effects
        return self.game_data.opp_poke_effects

    def clear_poke_effects(self, player):
        effects = self.game_data.poke_effects
        if player != self.player_num:
            effects = self.game_data.opp_poke_effects
        for eff in effects:
            effects[eff] = False

    def get_side_effects(self, player):
        if player == self.player_num:
            return self.game_data.side_effects
        return self.game_data.opp_side_effects

    def process_args(self, args, kwargs):
        if args[1] == 'player' and args[3] == self.player_name:
            #args[2] will be 'p1' or 'p2'
            self.player_num = args[2][1]
        if args[1] == 'request' and args[2] != '':
            #Read team data
            data = json.loads(args[2])
            if self.game_data.team == None:
                #Initialize team
                pokemon = list(map(Pokemon.from_data, data['side']['pokemon']))
                self.game_data.team = pokemon
                self.game_data.active = pokemon[0]
            else:
                #Update data
                for x in data['side']['pokemon']:
                    name,_,_ = Pokemon.get_details(x['details'])
                    for p in self.game_data.team:
                        if p.name == name:
                            h,m,s = Pokemon.get_condition(x['condition'])
                            p.health = h
                            p.max_health = m
                            p.status = s
                            p.stats = x['stats']
                            p.update_ability(x['ability'])
                            p.item = x['item']
                            break
            if 'wait' in data:
                self.wait_game = True
            else:
                if 'forceSwitch' in data:
                    self.wait_game = False
                    self.force_switch = True
                elif 'teamPreview' in data:
                    self.wait_game = False
                    self.choose_start = True
                else:
                    self.wait_game = False
                    self.force_switch = False
                    #Read active pokemon moves
                    moves = list(map(Move.from_data, data['active'][0]['moves']))
                    active = data['side']['pokemon'][0]
                    name,_,_ = Pokemon.get_details(active['details'])
                    for p in self.game_data.team:
                        if p.name == name:
                            p.moves = moves
        if args[1] == 'turn':
            #Do stuff with turn number?
            pass
        if args[1] == 'teamsize' and args[2] != 'p' + self.player_num:
            #Initialize opponent team with None for unknown pokemon
            num = int(args[3])
            self.game_data.opp_team = [None for i in range(num)]
        if args[1] == 'move':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                name = clean_name(args[3])
                #Check if zmove
                if name not in movedex:
                    #z status move
                    m = re.match('z(.*)', name)
                    name = m.group(1)
                    move_type = movedex[name]['type']
                    #Find corresponding zcrystal
                    for item in itemdex.values():
                        if 'zMoveType' in item and item['zMoveType'] == move_type:
                            self.game_data.opp_active.item = item['id']
                elif 'isZ' in movedex[name]:
                    zcrystal = movedex[name]['isZ']
                    if 'zMoveFrom' in itemdex[zcrystal]:
                        #Signature zmove
                        name = clean_name(itemdex[zcrystal]['zMoveFrom'])
                    else:
                        #Don't know original move
                        name = None
                    self.game_data.opp_active.item = zcrystal
                if name:
                    #Update opponent moves
                    opp_moves = self.game_data.opp_active.moves
                    for i in range(len(opp_moves)):
                        if opp_moves[i] == None:
                            opp_moves[i] = Move(name)
                            opp_moves[i].pp -= 1
                            break
                        if opp_moves[i].name == name:
                            opp_moves[i].pp -= 1
                            break
        if args[1] == 'switch' or args[1] == 'drag':
            player, nickname = parse_pokemon(args[2])
            if player == self.player_num:
                self.clear_boosts(self.player_num)
                self.clear_poke_effects(self.player_num)
                self.game_data.active.transformed = False
                #Update active pokemon and team positions
                name,_,_ = Pokemon.get_details(args[3])
                team = self.game_data.team
                if team:
                    for i in range(len(team)):
                        if team[i].name == name:
                            self.game_data.active = team[i]
                            team[0], team[i] = team[i], team[0]
                            break
            else:
                if self.game_data.opp_active:
                    self.game_data.opp_active.switch_out()
                self.clear_boosts(self.other_player())
                self.clear_poke_effects(self.other_player())
                #Update opponent active pokemon and team
                name,_,_ = Pokemon.get_details(args[3])
                for i in range(len(self.game_data.opp_team)):
                    opp = self.game_data.opp_team[i]
                    if opp == None:
                        #New pokemon
                        p = Pokemon.from_details(args[3], nickname, args[4])
                        self.game_data.opp_active = p
                        self.game_data.opp_team[i] = p
                        break
                    if name == opp.name:
                        #Existing pokemon
                        self.game_data.opp_active = opp
                        break
        if args[1] == 'detailschange' or args[1] == '-formechange':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                name,_,_ = Pokemon.get_details(args[3])
                self.game_data.opp_active.change_form(name)
        if args[1] == 'replace':
            #TODO: implement this
            pass
        if args[1] == 'faint':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                self.game_data.opp_active.status = 'fnt'
        if args[1] == '-damage' or args[1] == '-heal':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                health, max_health, status = Pokemon.get_condition(args[3])
                p = self.game_data.opp_active
                p.health = health
                p.max_health = max_health
                p.status = status
                self.check_item_ability(player, kwargs)
        if args[1] == '-sethp':
            player,_ = parse_pokemon(args[2])
            health1,_,_ = Pokemon.get_condition(args[3])
            health2,_,_= Pokemon.get_condition(args[5])
            if player == self.player_num:
                self.game_data.opp_active.health = health2
            else:
                self.game_data.opp_active.health = health1
        if args[1] == '-status':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                self.game_data.opp_active.status = args[3]
                self.check_item_ability(player, kwargs)
        if args[1] == '-curestatus':
            m = re.match('p(1|2): (.*)', args[2])
            if m:
                #Cured pokemon is not active
                if m.group(1) != self.player_num:
                    team = self.game_data.opp_team
                    for p in team:
                        if p.nickname == m.group(2):
                            p.status = None
                            break
            else:
                #Cured pokemon is active
                player,_ = parse_pokemon(args[2])
                if player != self.player_num:
                    self.game_data.opp_active.status = None
                    self.check_item_ability(player, kwargs)
        if args[1] == '-boost':
            player,_ = parse_pokemon(args[2])
            b = self.get_boosts(player)
            b[args[3]] += int(args[4])
            self.check_item_ability(player, kwargs)
        if args[1] == '-unboost':
            player,_ = parse_pokemon(args[2])
            b = self.get_boosts(player)
            b[args[3]] -= int(args[4])
            if player != self.player_num:
                self.check_item_ability(player, kwargs)
        if args[1] == '-setboost':
            player,_ = parse_pokemon(args[2])
            amount = int(args[4])
            #For some reason, anger point sends -setboost 12 instead of 6
            if amount > 6:
                amount = 6
            b = self.get_boosts(player)
            b[args[3]] = amount
            if player != self.player_num:
                self.check_item_ability(player, kwargs)
        if args[1] == '-swapboost':
            b = self.game_data.boosts
            opp_b = self.game_data.opp_boosts
            swap = list(b)
            if len(args) > 4:
                swap = args[4].split(', ')
            for stat in swap:
                b[stat], opp_b[stat] = opp_b[stat], b[stat]
        if args[1] == '-clearpositiveboost' or args[1] == '-clearnegativeboost':
            player,_ = parse_pokemon(args[2])
            b = self.get_boosts(player)
            for stat in b:
                if args[1] == '-clearpositiveboost' and b[stat] > 0:
                    b[stat] = 0
                elif args[1] == '-clearnegativeboost' and b[stat] < 0:
                    b[stat] = 0
            if player != self.player_num:
                self.check_item_ability(player, kwargs)
        if args[1] == '-copyboost':
            b_to = self.game_data.boosts
            b_from = self.game_data.opp_boosts
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                b_to, b_from = b_from, b_to
            swap = list(b_to)
            if len(args) > 4:
                swap = args[4].split(', ')
            for stat in b_to:
                b_to[stat] = b_from[stat]
        if args[1] == '-clearboost':
            player,_ = parse_pokemon(args[2])
            self.clear_boosts(player)
            if player != self.player_num:
                self.check_item_ability(player, kwargs)
        if args[1] == '-invertboost':
            player,_ = parse_pokemon(args[2])
            b = self.get_boosts(player)
            for stat in b:
                b[stat] = -b[stat]
            if player != self.player_num:
                self.check_item_ability(player, kwargs)
        if args[1] == '-clearallboost':
            self.clear_boosts(self.player_num)
            self.clear_boosts(self.other_player())
        if args[1] == '-item':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                self.game_data.opp_active.item = clean_name(args[3])
        if args[1] == '-enditem':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                self.game_data.opp_active.item = ''
        if args[1] == '-ability':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                ability = clean_name(args[3])
                self.game_data.opp_active.set_ability(ability)
        if args[1] == '-endability':
            player,_ = parse_pokemon(args[2])
            if player != self.player_num:
                opp = self.game_data.opp_active
                if len(args) <= 3:
                    opp.update_ability('')
                #Only remove ability if currently has ability
                #Needed because -endability is sent after using transform
                if len(args) > 3 and opp.ability == clean_name(args[3]):
                    opp.update_ability('')
        if args[1] == '-transform':
            player,_ = parse_pokemon(args[2])
            p = self.game_data.active
            opp = self.game_data.opp_active
            if player == self.player_num:
                self.game_data.boosts = self.game_data.opp_boosts.copy()
                #Update opponent data before transforming because
                #p.transform copies opponent data
                opp.set_ability(p.ability)
                opp.moves = []
                for move in p.moves:
                    opp.moves.append(Move(move.name))
                p.transform(opp)
            else:
                self.check_item_ability(player, kwargs)
                opp.transform(p)
                self.game_data.opp_boosts = self.game_data.boosts.copy()
        if args[1] == '-zpower':
            player,_ = parse_pokemon(args[2])
            if player == self.player_num:
                self.game_data.zmove = True
            else:
                self.game_data.opp_zmove = True
        if args[1] == '-mega':
            player,_ = parse_pokemon(args[2])
            if player == self.player_num:
                self.game_data.mega = True
            else:
                self.game_data.opp_mega = True
                self.game_data.opp_active.item = clean_name(args[4])
        if args[1] == '-start':
            player,_ = parse_pokemon(args[2])
            p = self.get_active(player)
            effects = self.get_poke_effects(player)
            m = re.match('(move: )?(.*)', args[3])
            eff = clean_name(m.group(2))
            if eff == 'typechange':
                if 'from' in kwargs:
                    arg = kwargs['from']
                    if arg == 'move: Reflect Type':
                        player2,_ = parse_pokemon(kwargs['of'])
                        p2 = self.get_active(player2)
                        p.types = p2.types.copy()
                    else:
                        if arg == 'Protean' or arg == 'Color Change':
                            p.set_ability(clean_name(arg))
                        new_type = clean_name(args[4])
                        p.types = [new_type]
                else:
                    new_type = clean_name(args[4])
                    p.types = [new_type]
            elif eff == 'typeadd':
                new_type = clean_name(args[4])
                p.types.append(new_type)
            elif eff in effects:
                effects[eff] = True
            else:
                self.logger.info('Unknown effect: %s', eff)
        if args[1] == '-end':
            player,_ = parse_pokemon(args[2])
            effects = self.get_poke_effects(player)
            m = re.match('(move: )?(.*)', args[3])
            eff = clean_name(m.group(2))
            if eff in effects:
                effects[eff] = False
            else:
                self.logger.info('Unknown effect: %s', eff)
        if args[1] == '-activate':
            player,_ = parse_pokemon(args[2])
            p = self.get_active(player)
            m = re.match('(?:(move|ability|item): )?(.*)', args[3])
            eff = clean_name(m.group(2))
            if m.group(1) == 'ability':
                p.set_ability(eff)
            elif m.group(1) == 'item':
                p.item = eff
            #Handle some special activations
            if eff == 'mummy':
                ofpoke = kwargs['of']
                ofplayer,_ = parse_pokemon(ofpoke)
                p2 = self.get_active(ofplayer)
                old_ability = clean_name(args[4])
                p2.set_ability(old_ability)
                p2.update_ability('mummy')
            elif eff == 'forewarn':
                name = clean_name(args[4])
                ofpoke = kwargs['of']
                ofplayer,_ = parse_pokemon(ofpoke)
                if ofplayer != self.player_num:
                    #Update opponent moves
                    opp_moves = self.game_data.opp_active.moves
                    for i in range(len(opp_moves)):
                        if opp_moves[i] == None:
                            opp_moves[i] = Move(name)
                            break
                        if opp_moves[i].name == name:
                            break
            elif eff == 'skillswap':
                ability1 = clean_name(args[4])
                ability2 = clean_name(args[5])
                ofpoke = kwargs['of']
                ofplayer,_ = parse_pokemon(ofpoke)
                p2 = self.get_active(ofplayer)
                p.set_ability(ability2)
                p.update_ability(ability1)
                p2.set_ability(ability1)
                p2.update_ability(ability2)
        if args[1] == '-sidestart':
            m = re.match('p(1|2): ', args[2])
            player = m.group(1)
            effects = self.get_side_effects(player)
            m = re.match('(move: )?(.*)', args[3])
            eff = clean_name(m.group(2))
            if eff == 'spikes' or eff == 'toxicspikes':
                effects[eff] += 1
            else:
                if eff in effects:
                    effects[eff] = True
        if args[1] == '-sideend':
            m = re.match('p(1|2): ', args[2])
            player = m.group(1)
            effects = self.get_side_effects(player)
            m = re.match('(move: )?(.*)', args[3])
            eff = clean_name(m.group(2))
            if eff == 'spikes' or eff == 'toxicspikes':
                effects[eff] = 0
            else:
                if eff in effects:
                    effects[eff] = False
        if args[1] == '-weather':
            weather = clean_name(args[2])
            if weather == 'none':
                self.game_data.weather = None
            else:
                self.game_data.weather = weather
                self.check_item_ability(self.player_num, kwargs)
        if args[1] == '-fieldstart':
            m = re.match('(move: )?(.*)', args[2])
            eff = clean_name(m.group(2))
            if eff.endswith('terrain'):
                self.game_data.terrain = eff
            else:
                if eff in self.game_data.field_effects:
                    self.game_data.field_effects[eff] = True
            self.check_item_ability(self.player_num, kwargs)
        if args[1] == '-fieldend':
            m = re.match('(move: )?(.*)', args[2])
            eff = clean_name(m.group(2))
            if eff.endswith('terrain'):
                self.game_data.terrain = None
            else:
                if eff in self.game_data.field_effects:
                    self.game_data.field_effects[eff] = False

    def check_item_ability(self, player, kwargs):
        if 'from' in kwargs:
            m = re.match('(item|ability): (.*)', kwargs['from'])
            if m:
                target = player
                if 'of' in kwargs:
                    target,_ = parse_pokemon(kwargs['of'])
                p = self.get_active(target)
                name = clean_name(m.group(2))
                if m.group(1) == 'item':
                    #Don't update if it's a berry, since they're consumed
                    #Not completely sure this always works
                    if not name.endswith('berry'):
                        p.item = name
                elif m.group(1) == 'ability':
                    p.set_ability(name)

    def move_to_features(self, move):
        #features: move index, type (18), category (3), power, accuracy,
        #priority, pp, target (7), disabled
        features = np.zeros(34)
        features[0] = self.move_to_ix[move.name]
        features[1 + self.types[move.move_type]] = 1
        features[19 + self.move_categories[move.category]] = 1
        features[22] = move.power
        features[23] = move.accuracy
        features[24] = move.priority
        features[25] = move.pp
        features[26 + self.move_targets[move.target]] = 1
        features[33] = move.disabled
        return features

    def poke_to_features(self, poke):
        #features: poke index, ability index, ability known,
        #base stats (6), types (18), level, health, max health, 
        #status (7), item index, item known, stats (5), stats known
        features = np.zeros(45)
        features[0] = self.poke_to_ix[poke.name]
        if poke.ability != None:
            features[1] = self.ability_to_ix[poke.ability]
            features[2] = 1
        features[3] = poke.base_stats['hp']
        features[4] = poke.base_stats['atk']
        features[5] = poke.base_stats['def']
        features[6] = poke.base_stats['spa']
        features[7] = poke.base_stats['spd']
        features[8] = poke.base_stats['spe']
        for t in poke.types:
            if t: #poke can be typeless
                features[9 + self.types[t]] = 1
        features[27] = poke.level
        features[28] = poke.health
        features[29] = poke.max_health
        if poke.status:
            features[30 + self.poke_statuses[poke.status]] = 1
        if poke.item != None:
            features[37] = self.item_to_ix[poke.item]
            features[38] = 1
        if poke.stats != None:
            features[39] = poke.stats['atk']
            features[40] = poke.stats['def']
            features[41] = poke.stats['spa']
            features[42] = poke.stats['spd']
            features[43] = poke.stats['spe']
            features[44] = 1
        return features

    def game_to_features(self):
        #features: own pokemon and poke known x6 (276),
        #opp pokemon and poke known x6 (276),
        #own moves and move known x4 (140),
        #opp moves and move known x4 (140),
        #own boosts (7), opp boosts (7), own poke effects (22),
        #opp poke effects (22), own side effects (11), opp side effects (11),
        #weathers (7), terrains (4), field effects (4),
        #mega, opp mega, zmove, opp zmove
        #Currently excluding moves of non-active pokemon from features
        features = np.zeros(931)
        fi = 0
        poke_len = 45
        for i in range(6):
            f = self.poke_to_features(self.game_data.team[i])
            features[fi:fi + poke_len] = f
            features[fi + poke_len] = 1
            fi += poke_len + 1
        for i in range(6):
            opp = self.game_data.opp_team[i]
            if opp != None:
                opp_f = self.poke_to_features(opp, True)
                features[fi:fi + poke_len] = opp_f
                features[fi + poke_len] = 1
            fi += poke_len + 1
        move_len = 34
        for i in range(4):
            f = self.move_to_features(self.game_data.active.moves[i])
            features[fi:fi + move_len] = f
            features[fi + move_len] = 1
            fi += move_len + 1
        for i in range(4):
            opp_move = self.game_data.opp_active.moves[i]
            if opp_move != None:
                opp_f = self.move_to_features(opp_move)
                features[fi:fi + move_len] = f
                features[fi + move_len ] = 1
            fi += move_len + 1
        features[fi:fi + 7] = self.game_data.boost_list()
        fi += 7
        features[fi:fi + 7] = self.game_data.opp_boost_list()
        fi += 7
        poke_eff_len = len(self.game_data.poke_effects_)
        for eff in self.game_data.poke_effects_:
            features[fi] = self.game_data.poke_effects[eff]
            features[fi + poke_eff_len] = self.game_data.opp_poke_effects[eff]
            fi += 1
        fi += poke_eff_len
        side_eff_len = len(self.game_data.side_effects_)
        for eff in self.game_data.side_effects_:
            features[fi] = self.game_data.side_effects[eff]
            features[fi + side_eff_len] = self.game_data.opp_side_effects[eff]
            fi += 1
        fi += side_eff_len
        if self.game_data.weather:
            i = self.game_data.weathers_.index(self.game_data.weather)
            features[fi + i] = 1
        fi += len(self.game_data.weathers_)
        if self.game_data.terrain:
            i = self.game_data.terrains_.index(self.game_data.terrain)
            features[fi + i] = 1
        fi += len(self.game_data.terrains_)
        for eff in self.game_data.field_effects_:
            features[fi] = self.game_data.field_effects[eff]
            fi += 1
        features[fi] = self.game_data.mega
        features[fi + 1] = self.game_data.opp_mega
        features[fi + 2] = self.game_data.zmove
        features[fi + 3] = self.game_data.opp_zmove
        return features
