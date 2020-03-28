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

from games import *
from streamers import *

# ==============================================================================
# Twitch API
# ==============================================================================

class TwitchAPI():

    def __init__(self, twitch_credentials):

        # Twitch uses OAuth2, so we need to grab an access_token
        params = {
            'client_id': twitch_credentials['client_id'],
            'client_secret': twitch_credentials['client_secret'],
            'grant_type': 'client_credentials'
        }
        r = requests.post("https://id.twitch.tv/oauth2/token", params=params)
        if (r.status_code == 200):
            data = r.json()
            self.headers = {'Authorization': 'Bearer ' + data['access_token']}
        else:
            self.headers = False

        # create headers for the deprecated v5 API
        self.v5API_headers = {'Client-ID': twitch_credentials['v5_client_id'], 'Accept': 'application/vnd.twitchtv.v5+json'}
        self.min_sleep_period = 1 / (800 / 60) # API has 800 requests per minute



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

    # the http header for responses from the Twitch API include the number of requests left before we reach our ratelimit
    # Twitch allows 800 requests per minute = ~13 requests per second
    # -> to be safe, when we run out wait an entire second
    def __sleep(self, header, min_sleep = 0):
        if (('ratelimit_remaining' in header) and (header['ratelimit_remaining'] == 0)):
            print('sleeping...', header['ratelimit_remaining'])
            time.sleep(1)
        elif (min_sleep > 0):
            time.sleep(min_sleep)


    # returns a tuple ([list of livestreams], pagination_cursor)
    # src: https://dev.twitch.tv/docs/api/reference#get-streams
    def get_livestreams(self, previous_cursor = False):
        livestreams = []
        cursor = False
        params = {} if (previous_cursor == False) else {'after': previous_cursor}
        params['first'] = '100'
        r = requests.get('https://api.twitch.tv/helix/streams', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            livestreams = data['data']
            if (('cursor' in data['pagination']) and (data['pagination']['cursor'] != '')):
                cursor = data['pagination']['cursor']

        self.__sleep(r.headers)
        return livestreams, cursor


    # takes in an list of streamer_ids and *always* returns a list of streamer objects (even if size 1 or 0)
    # src: https://dev.twitch.tv/docs/api/reference#get-users
    def get_streamers(self, streamer_ids):
        streamers = []
        params = self.__format_tuple_params(streamer_ids, 'id')
        r = requests.get('https://api.twitch.tv/helix/users', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            for streamer in data['data']:
                streamer['num_followers'] = self.get_followers(streamer['id'])
                streamer['id'] = int(streamer['id'])
                streamers.append(streamer)
        else:
            print("------------\nERROR")
            print(r.status_code)
            print(r.text)
            print("--------------")

        self.__sleep(r.headers)
        return streamers


    # gets a list of videos by a given streamer
    # src: https://dev.twitch.tv/docs/api/reference#get-videos
    def get_videos(self, streamer_id, previous_cursor = False, quantity = '100'):
        videos = []
        quantity = str(quantity) if (isinstance(quantity, int)) else quantity
        params = {'user_id': streamer_id, 'first': quantity}
        if (previous_cursor != False):
            params['after'] = previous_cursor
        r = requests.get('https://api.twitch.tv/helix/videos', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            for video in data['data']:
                video['game_name'] = self.get_game_name_in_video(video['id'])
                videos.append(video)
            cursor = False if ('cursor' not in data['pagination']) else data['pagination']['cursor']
        else:
            cursor = False
        self.__sleep(r.headers)
        return videos, cursor

    # returns the string name of a game played in a specified video
    # -> this uses the deprecated V5 API because the New API doesn't have this functionality
    # src: https://dev.twitch.tv/docs/v5/reference/videos#get-video
    def get_game_name_in_video(self, video_id):
        game = ""
        video_id = str(video_id) if (isinstance(video_id, int)) else video_id
        url = 'https://api.twitch.tv/kraken/videos/' + video_id
        r = requests.get(url, headers=self.v5API_headers)
        if (r.status_code == 200):
            data = r.json()
            game = data['game']
        else:
            self.sleep(r.headers, 2)
            return self.get_game_name_in_video(self, video_id)

        self.__sleep(r.headers)
        return game


    # gets the total # of followers for a given streamer
    # src: https://dev.twitch.tv/docs/api/reference#get-users-follows
    def get_followers(self, streamer_id):
        total = -1
        params = {'to_id': streamer_id}
        r = requests.get('https://api.twitch.tv/helix/users/follows', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            total = data['total']
        self.__sleep(r.headers)
        return total

    # takes in a list of game_ids and *always* returns a list of game objects (even if size 1)
    # src: https://dev.twitch.tv/docs/api/reference#get-games
    def get_games(self, game_ids):
        games = []
        params = self.__format_tuple_params(game_ids, 'id')
        r = requests.get('https://api.twitch.tv/helix/games', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            games = data['data']
        self.__sleep(r.headers)
        return games


# ==============================================================================
# IGDB API
# ==============================================================================

class IGDBAPI():

    def __init__(self, client_id):
        self.headers = {'user-key': client_id, 'Accept': 'application/json'}
        self.sleep_period = 0.075 # <- to be polite to IGDB's servers

    # searches the IGDB API for a game
    # if result_as_array=True, then return the entire list of results from the IGDB search
    # otherwise, return just the first object
    def search_for_game_by_name(self, game_name, result_as_array = False):
        time.sleep(self.sleep_period)
        games = []
        body = "search \"" + game_name + "\"; fields *;"
        r = requests.get('https://api-v3.igdb.com/games', data=body, headers=self.headers)
        if (r.status_code == 200):
            for game in r.json():
                game_id = game['id']
                covers = self.search_for_game_covers(max(game_id - 1, 1))
                if (game_id in covers):
                    game['igdb_box_art_url'] = covers[game_id]
                games.append(game)

        if (result_as_array == True):
            return games
        elif (len(games) > 0):
            return games[0]
        else:
            return False


    # searches for games with ids within range (offset, offset + 100)
    # returns tuple (list_of_games, new_offset)
    def search_for_games(self, offset = 0):
        time.sleep(self.sleep_period)

        games = []
        body = "fields *; sort id asc; limit 500; where id > " + str(offset) + ";"
        r = requests.get('https://api-v3.igdb.com/games', data=body, headers=self.headers)
        if (r.status_code == 200):

            game_covers = self.search_for_game_covers(offset)
            for game_id, cover in self.search_for_game_covers(offset + 125).items():
                game_covers[game_id] = cover
            for game_id, cover in self.search_for_game_covers(offset + 250).items():
                game_covers[game_id] = cover
            for game_id, cover in self.search_for_game_covers(offset + 375).items():
                game_covers[game_id] = cover

            for game in r.json():
                game_id = int(game['id'])
                game['igdb_box_art_url'] = game_covers[game_id] if (game_id in game_covers) else ""
                games.append(game)

        return games, offset + 500


    # searches for the cover of games with IDs within range (offset, offset + 125)
    # Note: 125 is arbitrarily picked so that there is ample room in the 500 results
    # -> this action can return multiple covers for the same game, so we will pick the largest one for each game
    # -> unlike .search_for_games(), this function returns a dictionary of form {'game_id': 'url'}
    def search_for_game_covers(self, offset = 0):
        time.sleep(self.sleep_period)

        covers_by_game = {}
        body = "fields *; sort game asc; limit 500; where game > " + str(offset) + " & game <= " + str(offset + 125) + ";"
        r = requests.get('https://api-v3.igdb.com/covers', data=body, headers=self.headers)
        if (r.status_code == 200):

            # bucket covers by game ID so we can compare sizes and keep the max
            for cover in r.json():
                game_id = int(cover['game'])

                if (('width' in cover) and ('height' in cover)):
                    cover_size = cover['width'] * cover['height']
                    if (game_id not in covers_by_game):
                        covers_by_game[game_id] = {'url': cover['url'], 'size': cover_size}
                    elif (cover_size > covers_by_game[game_id]['size']):
                        covers_by_game[game_id] = {'url': cover['url'], 'size': cover_size}

                elif (game_id not in covers_by_game): # <- account for rare cases where cover doesn't have size specs
                    covers_by_game[game_id] = {'url': cover['url'], 'size': 0}

            # remove the size metric
            for id in covers_by_game:
                covers_by_game[id] = 'https:' + covers_by_game[id]['url']


        return covers_by_game

# ==============================================================================
# Main Scraper
# ==============================================================================


# Compiling Games DB -----------------------------------------------------------

# scrapes games from IGDB into a Games collection
# -> this function runs without any interaction with the Twitch API, so it will leave certain parameters blank
#    (leaves twitch_box_art_url blank)
# limit defaults to an equivalent to +inf. Drop it to a low int for testing purposes (only get the first X=limit games)
# -> because of the way offset works, add 500 (size of an API result) to ensure the API returns all values up to the limit
def compile_games_db(igdb_credentials, limit = 9999999):

    igdbAPI = IGDBAPI(igdb_credentials)
    games = Games()

    # loop over all games on IGDB going in ascending order by ID
    offset = 0
    search_results, offset = igdbAPI.search_for_games(offset)
    while (len(search_results) > 0 and (offset < limit + 500)):
        for igdb_game_obj in search_results:
            games.add_new_game(igdb_game_obj)

        games.print_stats()
        search_results, offset = igdbAPI.search_for_games(offset)

    return games


# Scrape Streamers -------------------------------------------------------------

# scrapes all current livestreams on twitch and compiles them into a collection of Streamers
# -> loads pre-existing streamers from /data/streamers.csv
def compile_streamers_db(twitch_credentials, livestreams_limit = 9999999, videos_limit = 9999999):

    twitchAPI = TwitchAPI(twitch_credentials)
    streamers = Streamers() # <- LOAD STREAMERS FROM CSV FILE
    streams = get_all_livestreams(twitchAPI, livestreams_limit)

    # loop over livestreams to access streamers
    # -> we can look up streamer profiles in bulk (batches of 100 IDs)
    #    so we want to break our livestreams into batches
    batch_num = 0
    for batch in create_batches(streams, 100):

        print("BATCH ", batch_num)
        batch_num += 1

        # get a list of all streamer_ids for this batch
        streamer_ids = []
        stream_lookup = {}
        for stream in batch:
            streamer_ids.append(stream.user_id)
            stream_lookup[stream.user_id] = stream

        # search for streamer objects and create a lookup table {streamer_id -> streamer object}
        # -> These have updated values, so we'll do our stream analysis on these and then call Streamers.update()
        for user in twitchAPI.get_streamers(streamer_ids):
            user_id = user['id']
            stream = stream_lookup[user_id]
            user['language'] = stream.language

            # compile all livestreams/videos that the scraper hasn't already seen
            streamer_videos = [ stream_lookup[user_id] ]
            if (streamers.get(user_id) == False):
                print("scraping videos for streamer_id =", user_id)
                if (streamers.get(user_id) == False):
                    for video in get_all_videos_for_streamer(twitchAPI, user_id, videos_limit):
                        if (video.game_name != ""):
                            streamer_videos.append(video)
            print("# videos = ", len(streamer_videos))

            # add or update the streamer object w/ new profile info from twitch + stream data
            streamers.add_or_update_streamer(user)
            for stream in streamer_videos:
                streamers.add_stream_data(stream)


    return streamers


# returns all livestreams up to a limit
# -> uses a lookup table of already observed livestream IDs to make sure we know when to end
def get_all_livestreams(twitchAPI, limit = 9999999):

    print('\nScraping livestreams...')
    streams = []
    livestreams, cursor = twitchAPI.get_livestreams()
    livestream_ids = {}
    old_num_livestreams = -1
    while ((len(livestreams) > 0) and (len(streams) < limit) and (cursor != False) and (old_num_livestreams != len(livestream_ids))):
        old_num_livestreams = len(livestream_ids)

        for livestream in livestreams:
            if (len(streams) < limit):
                stream = Stream(livestream)
                if (stream.id not in livestream_ids):
                    streams.append(stream)
                    livestream_ids[stream.id] = 1

        print("livestreams: ", len(livestream_ids))
        livestreams, cursor = twitchAPI.get_livestreams(cursor)
    return streams


def get_all_videos_for_streamer(twitchAPI, streamer_id, limit = 9999999):
    all_videos = []
    videos, cursor = twitchAPI.get_videos(streamer_id)
    while ((len(videos) > 0) and (len(all_videos) < limit)):
        for video in videos:
            all_videos.append(Stream(video, False))
        videos, cursor = twitchAPI.get_videos(streamer_id, cursor)
    return all_videos

# takes in a list of items l
# returns a list of n batch_sized lists with items distributed into batches
# ex: given l=[1, 2, 3, 4, 5] and batch_size=2
#    -> [ [1, 2], [3, 4], [5] ]
def create_batches(l, batch_size):
    new_list = []
    i = 0
    new_list.append([])
    for item in l:
        if (len(new_list[i]) >= batch_size):
            new_list.append([])
            i += 1
        else:
            new_list[i].append(item)
    return new_list


# Main -------------------------------------------------------------------------

# Run the main scraper
def run():

    # get secret API clientIDs
    credentials = open('credentials.json')
    credentials = json.load(credentials)

    # scrape the IGDB database for games
    if (("-g" in sys.argv) or ("--games" in sys.argv)):
        igdbGames = compile_games_db(credentials['igdb'])
        igdbGames.export_to_csv('./data/games.csv')
        igdbGames.print_stats()


    if (("-s" in sys.argv) or ("--streamers" in sys.argv)):
        streamers = compile_streamers_db(credentials['twitch'])
        streamers.export_to_csv('./data/streamers.csv')

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
