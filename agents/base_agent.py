import random
import logging
import json
import re
from pokemon import Pokemon, Move, GameData, clean_name
from dex import movedex, itemdex

def parse_pokemon(s):
    """Get player num and pokemon nickname"""
    m = re.match('p(1|2)a: (.*)', s)
    return m.group(1), m.group(2)

class Agent:
    def __init__(self, player_name):
        self.player_name = player_name
        self.player_num = None
        self.logger = logging.getLogger(__name__)
        if len(self.logger.handlers) == 0:
            self.logger.addHandler(logging.StreamHandler())
        self.game_data = GameData()
        self.wait_game = True
        self.force_switch = False
        self.choose_start = False

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
                    p.item = name
                elif m.group(1) == 'ability':
                    p.set_ability(name)
