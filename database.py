import json
import sqlite3


""" ############### Loading the settings json config file ############### """
config_file = None
with open('settings.json') as json_file:
    config_file = json.load(json_file)

""" ####################### Loading rooms info ########################## """
rooms_name = config_file['rooms_name']
rooms_min_bet = config_file['rooms_min_bet']
rooms_max_bet = config_file['rooms_max_bet']
rooms_active_players = [0] * len(config_file['rooms_name'])

conn = sqlite3.connect('sharex.db')
c = conn.cursor()

def get_rooms_full_info():
    return {
            "TYPE"  : "FULL_ROOMS_INFO",
            "NAMES" : rooms_name,
            "MINBET": rooms_min_bet,
            "MAXBET": rooms_max_bet,
            "ACTIVE": rooms_active_players
            }

def get_rooms_active_players_info():
    return {
            "TYPE"  : "ACTIVIY_ROOMS_INFO",
            "ACTIVE": rooms_active_players
            }
