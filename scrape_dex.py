from selenium import webdriver
import os

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(chrome_options=options)
driver.get('https://dex.pokemonshowdown.com')
pokedex = driver.execute_script('return JSON.stringify(BattlePokedex)')
movedex = driver.execute_script('return JSON.stringify(BattleMovedex)')
itemdex = driver.execute_script('return JSON.stringify(BattleItems)')
driver.quit()
with open('pokedex.json', 'w') as f:
    f.write(pokedex)
with open('movedex.json', 'w') as f:
    f.write(movedex)
with open('itemdex.json', 'w') as f:
    f.write(itemdex)
