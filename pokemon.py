import re
from dex import pokedex, movedex

def clean_name(s):
    """Removes non-alphanumeric characters and turns to lowercase"""
    return re.sub('[\W_]+', '', s).lower()

class Move:
    def __init__(self, name, pp=None, disabled=False):
        #For some reason hidden power adds a '60' at the end of the move name
        #in the console, but not in the movedex
        m = re.match('(hiddenpower.*)60', name)
        if m:
            name = m.group(1)
        self.name = name
        data = movedex[name]
        self.move_type = data['type']
        self.category = data['category']
        self.power = data['basePower']
        self.accuracy = data['accuracy']
        self.priority = data['priority']
        self.maxpp = int(data['pp'] * 1.6)
        self.pp = pp or self.maxpp
        #Some target types are only different in doubles mode
        target_normal = ['any', 'allAdjacentFoes', 'scripted', 'normal',
            'allAdjacent', 'adjacentFoe','randomNormal']
        target_self = ['adjacentAllyOrSelf', 'self']
        target = data['target']
        if target in target_normal:
            target = 'normal'
        elif target in target_self:
            target = 'self'
        self.target = target
        self.disabled = disabled

    @classmethod
    def from_data(cls, data):
        name = data['id']
        pp = data.get('pp') #Could be None
        disabled = data.get('disabled', False)
        return cls(name, pp, disabled)

    def __str__(self):
        return '{} pp={}/{}'.format(self.name, self.pp, self.maxpp)

class Pokemon:
    def __init__(self, name, level, gender, nickname, health, max_health, status,
            moves, stats=None, base_ability=None, ability=None, item=None):
        #NOTE: For attributes, None means unknown, '' means none
        self.name = name
        data = pokedex[name]
        self.abilities = list(map(clean_name, data['abilities']))
        self.base_stats = data['baseStats']
        self.types = list(map(clean_name, data['types']))
        self.level = level
        self.gender = gender
        self.nickname = nickname
        self.health = health
        self.max_health = max_health
        self.status = status
        self.moves = moves
        self.stats = stats
        self.base_ability = base_ability
        self.ability = ability
        if base_ability == None and ability == None and len(self.abilities) == 1:
            self.base_ability = self.abilities[0]
            self.ability = self.abilities[0]
        self.item = item 
        self.transformed = False
        self.moves_backup = None

    @staticmethod
    def get_details(details):
        m = re.match('([^,]*)(?:, L(\d+))?(?:, ([MF]))?', details)
        name = clean_name(m.group(1))
        level = int(m.group(2)) if m.group(2) else 100
        gender = m.group(3)
        return name, level, gender

    @staticmethod
    def get_condition(condition):
        m = re.match('(\d+)(?:/(\d+))?(?: ([a-z]{3}))?', condition)
        health = int(m.group(1))
        max_health = int(m.group(2)) if m.group(2) else 0
        status = m.group(3)
        return health, max_health, status

    @classmethod
    def from_data(cls, data):
        name, level, gender = Pokemon.get_details(data['details'])
        nickname = re.match('p(1|2): (.*)', data['ident']).group(2)
        health, max_health, status = Pokemon.get_condition(data['condition'])
        stats = data['stats']
        moves = list(map(Move, data['moves']))
        base_ability = data['baseAbility']
        ability = base_ability
        item = data['item']
        return cls(name, level, gender, nickname, health, max_health, status,
            moves, stats, base_ability, ability, item)

    @classmethod
    def from_details(cls, details, nickname, condition):
        name, level, gender = Pokemon.get_details(details)
        health, max_health, status = Pokemon.get_condition(condition)
        moves = [None, None, None, None]
        return cls(name, level, gender, nickname, health, max_health, status, moves)

    def change_form(self, name):
        self.name = name
        data = pokedex[name]
        self.abilities = list(map(clean_name, data['abilities']))
        self.base_stats = data['baseStats']
        self.types = list(map(clean_name, data['types']))
        if len(self.abilities) == 1:
            self.base_ability = self.abilities[0]
            self.ability = self.abilities[0]
        else:
            self.base_ability = None
            self.ability = None

    def set_ability(self, ability):
        #Updates base_ability if it doesn't exist
        if self.base_ability == None:
            self.base_ability = ability
        self.ability = ability

    def update_ability(self, ability):
        #Changes ability without updating base_ability
        self.ability = ability

    def switch_out(self):
        if self.transformed:
            self.transformed = False
            self.moves = self.moves_backup
        self.ability = self.base_ability
        data = pokedex[self.name]
        self.base_stats = data['baseStats']
        self.types = list(map(clean_name, data['types']))

    def transform(self, pokemon):
        self.transformed = True
        self.ability = pokemon.ability
        self.types = pokemon.types.copy()
        self.moves_backup = self.moves
        self.moves = []
        for move in pokemon.moves:
            copy = Move(move.name, 5)
            copy.maxpp = 5
            self.moves.append(copy)
        for stat in pokemon.base_stats:
            if stat != 'hp':
                self.base_stats[stat] = pokemon.base_stats[stat]

    def __str__(self):
        d = {}
        d['name'] = self.name
        d['types'] = self.types
        d['health'] = self.health
        d['max_health'] = self.max_health
        d['status'] = self.status
        d['moves'] = list(map(str, self.moves))
        d['base_ability'] = self.base_ability
        d['ability'] = self.ability
        d['item'] = self.item
        return str(d)

class GameData:
    def __init__(self):
        boosts = ['atk', 'def', 'spa', 'spd', 'spe', 'accuracy', 'evasion']
        poke_effects = ['confusion', 'curse', 'embargo', 'encore', 'healblock',
            'foresight', 'miracleeye', 'attract', 'leechseed', 'nightmare',
            'perish3', 'perish2', 'perish1', 'taunt', 'telekinesis', 'torment',
            'aquaring', 'ingrain', 'magnetrise', 'powertrick', 'focusenergy',
            'substitute']
        side_effects = ['stealthrock', 'spikes', 'toxicspikes', 'stickyweb',
            'tailwind', 'auroraveil', 'reflect', 'lightscreen', 'safeguard',
            'mist', 'luckychant']
        weathers = ['sunnyday', 'desolateland', 'raindance', 'primordialsea',
            'sandstorm', 'hail', 'deltastream']
        terrains = ['electricterrain', 'grassyterrain', 'mistyterrain', 'psychicterrain']
        field_effects = ['wonderroom', 'magicroom', 'trickroom', 'gravity']
        self.team = None
        self.active = None
        self.mega = False
        self.zmove = False
        self.boosts = {stat:0 for stat in boosts}
        self.poke_effects = {eff:False for eff in poke_effects}
        self.side_effects = {eff:False for eff in side_effects}
        self.side_effects['spikes'] = 0
        self.side_effects['toxicspikes'] = 0
        self.opp_team = None
        self.opp_active = None
        self.opp_mega = False
        self.opp_zmove = False
        self.opp_boosts = {stat:0 for stat in boosts}
        self.opp_poke_effects = {eff:False for eff in poke_effects}
        self.opp_side_effects = {eff:False for eff in side_effects}
        self.opp_side_effects['spikes'] = 0
        self.opp_side_effects['toxicspikes'] = 0
        self.weather = None
        self.terrain = None
        self.field_effects = {eff:False for eff in field_effects}

    def boost_list(self):
        boosts = ['atk', 'def', 'spa', 'spd', 'spe', 'accuracy', 'evasion']
        return [self.boosts[stat] for stat in boosts]

    def opp_boost_list(self):
        boosts = ['atk', 'def', 'spa', 'spd', 'spe', 'accuracy', 'evasion']
        return [self.opp_boosts[stat] for stat in boosts]
