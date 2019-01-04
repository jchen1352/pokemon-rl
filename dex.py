import json
import re

def clean_name(s):
    """Removes non-alphanumeric characters and turns to lowercase"""
    return re.sub('[\W_]+', '', s).lower()

def list_attrs(dex):
    a = set()
    for x in dex.values():
        a = set.union(a,x)
    return sorted(list(a))

def find(dex, attr):
    return [x for x in dex if attr in dex[x]]

#Open pokedex file
with open('pokedex.json') as f:
    pokedex = json.load(f)

#Remove nonstandard pokemon
remove = find(pokedex, 'isNonstandard')
for r in remove:
    pokedex.pop(r)

#Only keep attributes that affect battling
attrs = ['abilities','baseStats','types']
for p in pokedex:
    #Make abilities a list, remove unreleased hidden abilities, clean names
    if 'unreleasedHidden' in pokedex[p]:
        pokedex[p]['abilities'].pop('H')
    a = list(map(clean_name, pokedex[p]['abilities'].values()))
    pokedex[p]['abilities'] = a
    #Clean type names
    pokedex[p]['types'] = list(map(clean_name, pokedex[p]['types']))
    pokedex[p] = {x:pokedex[p][x] for x in attrs}

#Open movedex file
with open('movedex.json') as f:
    movedex = json.load(f)

#Remove nonstandard and unreleased moves
remove = find(movedex, 'isNonstandard') + find(movedex, 'isUnreleased')
for r in remove:
    movedex.pop(r)

#Add 'recharge' as a move that does nothing
movedex['recharge'] = {'accuracy':True, 'basePower':0, 'category':'Status',
    'id':'recharge', 'name':'Recharge', 'pp':30, 'priority':0, 'target':'self',
    'type':'Normal'}

#Open itemdex file
with open('itemdex.json') as f:
    itemdex = json.load(f)

#Remove nonstandard and unreleased items
remove = find(itemdex, 'isNonstandard') + find(itemdex, 'isUnreleased')
for r in remove:
    itemdex.pop(r)

#Create unique indices for pokemon, moves, items and abilities
poke_to_ix = {poke:i for i, poke in enumerate(pokedex)}
move_to_ix = {move:i for i, move in enumerate(movedex)}
#Assign index 0 to having no item
item_to_ix = {item:i+1 for i, item in enumerate(itemdex)}
item_to_ix[''] = 0
#Get all abilities
abilities = set()
for p in pokedex:
    for a in pokedex[p]['abilities']:
        abilities.add(clean_name(a))
#Assign index 0 to having no ability
ability_to_ix = {a:i+1 for i, a in enumerate(abilities)}
ability_to_ix[''] = 0

__all__ = ['pokedex', 'movedex', 'itemdex', 'poke_to_ix', 'move_to_ix',
    'item_to_ix', 'ability_to_ix', 'clean_name']
