# ==============================================================================
# About
# ==============================================================================
#
# scraper.py is a script for scraping IndieOutreach's streamer and games content from Twitch and IGDB
# It saves data to .CSV files
#

# Imports ----------------------------------------------------------------------

import sys
import json
import time
import requests

# ==============================================================================
# Twitch API
# ==============================================================================

class TwitchAPI():

    def __init__(self, client_id):
        self.headers = {'Client-ID': client_id}
        self.sleep_period = 0.1

    # takes in a list of items and converts it into a list of tuples
    # [streamer_id, streamer_id2, ...] -> [(id, streamer_id), (id, streamer_id2), ...]
    def __format_tuple_params(self, items, key):
        params = []
        if (isinstance(items, list)):
            for id in items:
                params.append((key, id))
        else:
            params.append((key, items))

        return params


    # returns a tuple ([list of livestreams], pagination_cursor)
    # src: https://dev.twitch.tv/docs/api/reference#get-streams
    def get_livestreams(self, previous_cursor = False):
        time.sleep(self.sleep_period)

        livestreams = []
        cursor = False
        params = {} if (previous_cursor == False) else {'after': previous_cursor}
        params['first'] = '100'
        r = requests.get('https://api.twitch.tv/helix/streams', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            livestreams = data['data']
            cursor = data['pagination']['cursor']
        return livestreams, cursor


    # takes in an list of streamer_ids and *always* returns a list of streamer objects (even if size 1 or 0)
    # src: https://dev.twitch.tv/docs/api/reference#get-users
    def get_streamers(self, streamer_ids):
        time.sleep(self.sleep_period)

        streamers = []
        params = self.__format_tuple_params(streamer_ids, 'id')
        r = requests.get('https://api.twitch.tv/helix/users', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            streamers = data['data']

        return streamers


    # gets a list of videos by a given streamer
    # src: https://dev.twitch.tv/docs/api/reference#get-videos
    def get_videos(self, streamer_id, previous_cursor = False, quantity = '100'):
        time.sleep(self.sleep_period)

        quantity = str(quantity) if (isinstance(quantity, int)) else quantity
        params = {'user_id': streamer_id, 'first': quantity}
        if (previous_cursor != False):
            params['after'] = previous_cursor
        r = requests.get('https://api.twitch.tv/helix/videos', params=params, headers=self.headers)
        data = r.json()
        videos = data['data']
        cursor = False if ('cursor' not in data['pagination']) else data['pagination']['cursor']
        return videos, cursor


    # gets the total # of followers for a given streamer
    # src: https://dev.twitch.tv/docs/api/reference#get-users-follows
    def get_followers(self, streamer_id):
        time.sleep(self.sleep_period)

        total = -1
        params = {'to_id': streamer_id}
        r = requests.get('https://api.twitch.tv/helix/users/follows', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            total = data['total']
        return total

    # takes in a list of game_ids and *always* returns a list of game objects (even if size 1)
    # src: https://dev.twitch.tv/docs/api/reference#get-games
    def get_games(self, game_ids):
        time.sleep(self.sleep_period)

        games = []
        params = self.__format_tuple_params(game_ids, 'id')
        r = requests.get('https://api.twitch.tv/helix/games', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            games = data['data']
        return games


# ==============================================================================
# IGDB API
# ==============================================================================

class IGDBAPI():

    def __init__(self, client_id):
        self.headers = {'user-key': client_id, 'Accept': 'application/json'}
        self.sleep_period = 0.01

    # searches the IGDB API for a game
    # if result_as_array=True, then return the entire list of results from the IGDB search
    # otherwise, return just the first object
    def search_for_game_by_name(self, game_name, result_as_array = False):
        time.sleep(self.sleep_period)
        games = []
        body = "search \"" + game_name + "\"; fields *;"
        r = requests.get('https://api-v3.igdb.com/games', data=body, headers=self.headers)
        if (r.status_code == 200):
            games = r.json()

        if (result_as_array == True):
            return games
        elif (len(games) > 0):
            return games[0]
        else:
            return False


    # searches for games with ids within range (offset, offset + 100)
    def search_for_games(self, offset = 0):
        time.sleep(self.sleep_period)
        
        games = []
        body = "fields *; sort id asc; limit 100; offset " + str(offset) + ";"
        r = requests.get('https://api-v3.igdb.com/games', data=body, headers=self.headers)
        if (r.status_code == 200):
            games = r.json()

        return games

# ==============================================================================
# Main Scraper
# ==============================================================================

# scrapes games and stores them in a CSV file
# -> this function runs without any interaction with the Twitch API, so it will leave certain parameters blank
#    (leaves twitch_box_art_url blank)
def compile_games_db(igdbCredentials):

    igdbAPI = IGDBAPI(igdbCredentials)

    print("hello world")


# Run the main scraper
def run():

    # get secret API clientIDs
    credentials = open('credentials.json')
    credentials = json.load(credentials)

    # initialize the Twitch and IGDB APIs
    twitchAPI = TwitchAPI(credentials['twitch'])
    igdbAPI = IGDBAPI(credentials['igdb'])



# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
