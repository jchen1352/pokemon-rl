import json

def list_attrs(dex):
    a = set()
    for x in dex.values():
        a = set.union(a,x)
    return sorted(list(a))

def find(dex, attr):
    return [x for x in dex if attr in dex[x]]

with open('pokedex.json') as f:
    pokedex = json.load(f)

#Remove nonstandard pokemon
remove = find(pokedex, 'isNonstandard')
for r in remove:
    pokedex.pop(r)

#Only keep attributes that affect battling
attrs = ['abilities','baseStats','types']
for p in pokedex:
    #Make abilities a list, remove unreleased hidden abilities
    if 'unreleasedHidden' in pokedex[p]:
        pokedex[p]['abilities'].pop('H')
    pokedex[p]['abilities'] = list(pokedex[p]['abilities'].values())
    pokedex[p] = {x:pokedex[p][x] for x in attrs}

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

with open('itemdex.json') as f:
    itemdex = json.load(f)

#Remove nonstandard and unreleased items
remove = find(itemdex, 'isNonstandard') + find(itemdex, 'isUnreleased')
for r in remove:
    itemdex.pop(r)
