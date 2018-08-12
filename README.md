# Pokemon RL

This repository contains code that will allow for reinforcement learning on the game of Pokemon. It will also allow for automatic online playing, via Selenium Webdriver.

## Requirements

Currently only works on Unix and requires Google Chrome/Chromium.
Requires Python Selenium Webdriver (install with `pip install selenium`)

## Installing and Running

To clone this repository and the Pokemon-Showdown submodule, use

```
git clone --recurse-submodules https://github.com/jchen1352/pokemon-rl.git
```

Follow the instructions on the Pokemon-Showdown github page to install it.

First get JSON data files by running `python scrape_dex.py`.

To simulate a battle between two bots, run `python sim.py [p1name] [p2name]`.

To use the bot to play online, run `python browser.py [username] [password]`. Alternatively, create a file named `login.json` in the following format to eliminate the need to pass in your username and password manually:

```
{
    "username":"[your username]",
    "password":"[your password]",
}
```

To run unit tests, run `python test.py`.

## Training the Agent

Not implemented yet
