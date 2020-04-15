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
import math
import requests
import argparse
import datetime

from logs import *
from games import *
from streamers import *
from insights import *

# ==============================================================================
# Twitch API
# ==============================================================================

class TwitchAPI():

    def __init__(self, twitch_credentials, print_errors = False):

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
        self.print_errors = print_errors

        # initialize TimeLogs
        request_types = ['get_livestreams', 'get_streamers', 'get_videos', 'get_game_name_in_video', 'get_followers', 'get_games']
        self.request_logs = TimeLogs(request_types)


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
        if (('ratelimit_remaining' in header) and (header['ratelimit_remaining'] <= 1)):
            print('sleeping...', header['ratelimit_remaining'])
            time.sleep(1)
        elif (min_sleep > 0):
            time.sleep(min_sleep)


    # returns a tuple ([list of livestreams], pagination_cursor)
    # src: https://dev.twitch.tv/docs/api/reference#get-streams
    def get_livestreams(self, previous_cursor = False):
        self.request_logs.start_action('get_livestreams')
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
        self.request_logs.end_action('get_livestreams')
        return livestreams, cursor


    # takes in an list of streamer_ids and *always* returns a list of streamer objects (even if size 1 or 0)
    # src: https://dev.twitch.tv/docs/api/reference#get-users
    def get_streamers(self, streamer_ids):
        self.request_logs.start_action('get_streamers')
        streamers = []
        params = self.__format_tuple_params(streamer_ids, 'id')
        r = requests.get('https://api.twitch.tv/helix/users', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            for streamer in data['data']:
                streamer['follower_counts'] = []
                streamer['id'] = int(streamer['id'])
                streamers.append(streamer)
        else:
            if (self.print_errors):
                print("------------\nERROR in TwitchAPi.get_livestreams()")
                print(r.status_code)
                print(r.text)
                print(streamer_ids)
                print("--------------")

        self.__sleep(r.headers)
        self.request_logs.end_action('get_streamers')
        return streamers


    # gets a list of videos by a given streamer
    # src: https://dev.twitch.tv/docs/api/reference#get-videos
    def get_videos(self, streamer_id, previous_cursor = False, quantity = '100'):
        self.request_logs.start_action('get_videos')
        videos = []

        # quantity should be an int with value <= 100 and converted into a string
        quantity = int(quantity)
        quantity = quantity if (quantity <= 100) else 100
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
        self.request_logs.end_action('get_videos')
        return videos, cursor

    # returns the string name of a game played in a specified video
    # -> this uses the deprecated V5 API because the New API doesn't have this functionality
    # src: https://dev.twitch.tv/docs/v5/reference/videos#get-video
    def get_game_name_in_video(self, video_id):
        self.request_logs.start_action('get_game_name_in_video')
        game = ""
        video_id = str(video_id) if (isinstance(video_id, int)) else video_id
        url = 'https://api.twitch.tv/kraken/videos/' + video_id
        r = requests.get(url, headers=self.v5API_headers)
        if (r.status_code == 200):
            data = r.json()
            game = data['game']
        elif (r.status_code == 429): # <- too many requests
            self.__sleep(r.headers, 2)
            return self.get_game_name_in_video(self, video_id)

        self.__sleep(r.headers)
        self.request_logs.end_action('get_game_name_in_video')
        return game


    # gets the total # of followers for a given streamer
    # src: https://dev.twitch.tv/docs/api/reference#get-users-follows
    def get_followers(self, streamer_id):
        self.request_logs.start_action('get_followers')
        total = -1
        params = {'to_id': streamer_id}
        r = requests.get('https://api.twitch.tv/helix/users/follows', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            total = data['total']
        self.__sleep(r.headers)
        self.request_logs.end_action('get_followers')
        return total

    # takes in a list of game_ids and *always* returns a list of game objects (even if size 1)
    # src: https://dev.twitch.tv/docs/api/reference#get-games
    def get_games(self, game_ids):
        self.request_logs.start_action('get_games')
        games = []
        params = self.__format_tuple_params(game_ids, 'id')
        r = requests.get('https://api.twitch.tv/helix/games', params=params, headers=self.headers)
        if (r.status_code == 200):
            data = r.json()
            games = data['data']
        self.__sleep(r.headers)
        self.request_logs.end_action('get_games')
        return games


# ==============================================================================
# IGDB API
# ==============================================================================

class IGDBAPI():

    def __init__(self, client_id):
        self.headers = {'user-key': client_id, 'Accept': 'application/json'}
        self.sleep_period = 0.075 # <- to be polite to IGDB's servers

        request_types = ['search_for_game_by_name', 'search_for_games', 'search_for_game_covers']
        self.request_logs = TimeLogs(request_types)


    # searches the IGDB API for a game
    # if result_as_array=True, then return the entire list of results from the IGDB search
    # otherwise, return just the first object
    def search_for_game_by_name(self, game_name, result_as_array = False):
        self.request_logs.start_action('search_for_game_by_name')
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
        else:
            print('Error in IGDBAPI.search_for_game_by_name()')
            print(r.status_code)
            print(r.text)

        self.request_logs.end_action('search_for_game_by_name')
        if (result_as_array == True):
            return games
        elif (len(games) > 0):
            return games[0]
        else:
            return False


    # searches for games with ids within range (offset, offset + 100)
    # returns tuple (list_of_games, new_offset)
    def search_for_games(self, offset = 0):
        self.request_logs.start_action('search_for_games')
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
        else:
            print('Error in IGDBAPI.search_for_games()')
            print(r.status_code)
            print(r.text)

        self.request_logs.end_action('search_for_games')
        return games, offset + 500


    # searches for the cover of games with IDs within range (offset, offset + 125)
    # Note: 125 is arbitrarily picked so that there is ample room in the 500 results
    # -> this action can return multiple covers for the same game, so we will pick the largest one for each game
    # -> unlike .search_for_games(), this function returns a dictionary of form {'game_id': 'url'}
    def search_for_game_covers(self, offset = 0):
        self.request_logs.start_action('search_for_game_covers')
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

        else:
            print('Error in IGDBAPI.search_for_game_covers')
            print(r.status_code)
            print(r.text)
        self.request_logs.end_action('search_for_game_covers')
        return covers_by_game

# ==============================================================================
# Main Scraper
# ==============================================================================


class Scraper():

    def __init__(self, credentials, mode = 'cli'):
        self.twitchAPI = TwitchAPI(credentials['twitch'])
        self.igdbAPI = IGDBAPI(credentials['igdb'])
        self.print_mode_on = True
        self.filterLogs = FilterLogs()
        self.set_mode(mode)
        return

    # lets user activate a different mode
    def set_mode(self, mode):
        current_month = datetime.datetime.now().strftime("%Y-%m")

        if (mode == 'cli'):
            self.mode = 'cli'
            self.filepaths = {
                'games': './data/games.csv',
                'streamers': './data/streamers',
                'streamers_missing_videos': './data/streamers_missing_videos.csv',
                'logs': './logs/requests[' + current_month + '].csv',
                'filterlogs': './logs/filters[' + current_month + '].csv'
            }
            self.insights = Insights('cli')
            self.insights.set_logging(True)

        elif (mode == 'testing'):
            self.mode = 'testing'
            self.filepaths = {
                'games': './test/games.csv',
                'streamers': './test/streamers',
                'streamers_missing_videos': './test/streamers_missing_videos.csv',
                'logs': './test/requests[' + current_month + '].csv',
                'filterlogs': './test/filterlogs[' + current_month + '].csv'
            }
            self.insights = Insights('testing')
            self.insights.set_logging(True)

        elif (mode == 'production'):
            self.mode = 'production'
            self.filepaths = {
                'games': './data/games.csv',
                'streamers': './data/streamers',
                'streamers_missing_videos': './data/streamers_missing_videos.csv',
                'logs': './logs/requests[' + current_month + '].csv',
                'filterlogs': './logs/filters[' + current_month + '].csv'
            }
            self.print_mode_on = False

        # save any log changes and load the new logs object
        self.filterLogs.export_to_csv()
        self.filterLogs = FilterLogs(self.filepaths['filterlogs'])


    def reload_filter_logs(self):
        self.filterLogs.export_to_csv()
        current_month = datetime.datetime.now().strftime("%Y-%m")
        if (current_month != self.filterLogs.month):
            if ((self.mode == 'production') or (self.mode == 'cli')):
                self.filterLogs = FilterLogs('/logs/filters[' + current_month + '].csv')
            elif (self.mode == 'testing'):
                self.filterLogs = FilterLogs('/test/filters.csv')


    # prints if the mode is right
    def __print(self, message):
        if (self.print_mode_on):
            print(message)

    def set_print_mode(self, print_mode):
        self.print_mode_on = print_mode

    # updates which files Scraper points at
    def update_filepaths(filetype, filepath):
        self.filepaths[filetype] = filepath

    # Compiling Games DB -------------------------------------------------------

    # scrapes games from IGDB into a Games collection
    # -> this function runs without any interaction with the Twitch API, so it will leave certain parameters blank
    #    (leaves twitch_box_art_url blank)
    # limit defaults to an equivalent to +inf. Drop it to a low int for testing purposes (only get the first X=limit games)
    # -> because of the way offset works, add 500 (size of an API result) to ensure the API returns all values up to the limit
    def compile_games_db(self, limit = 9999999):

        games = Games() # <- MODIFY THIS TO load existing games DB './data/games.csv'

        # loop over all games on IGDB going in ascending order by ID
        offset = 0
        search_results, offset = self.igdbAPI.search_for_games(offset)
        while (len(search_results) > 0 and (offset < limit + 500)):
            for igdb_game_obj in search_results:
                games.add_new_game(igdb_game_obj)

            if (self.mode == 'cli'):
                games.print_stats()
            search_results, offset = self.igdbAPI.search_for_games(offset)

        if (self.mode == 'cli'):
            self.igdbAPI.request_logs.print_stats()
            num_games = len(games.get_ids())
            self.igdbAPI.request_logs.export_to_csv(self.filepaths['logs'], 'games', num_games)
            games.export_to_csv(self.filepaths['games'])
        return games


    # Scrape Streamers ---------------------------------------------------------

    # scrapes all current livestreams on twitch and compiles them into a collection of Streamers
    # -> does NOT add video data to streamers because of runtime concerns
    # -> If necessary, loads pre-existing streamers from /data/streamers.csv
    def compile_streamers_db(self, streamers = False, livestreams_limit = 9999999):

        # load existing streamers
        if (streamers == False):
            streamers = Streamers(self.filepaths['streamers'], self.filepaths['streamers_missing_videos'])
            self.__print('Starting with ' + str(len(streamers.get_ids())) + ' streamers from CSV file')


        # get all livestreams currently on Twitch
        streams = self.get_all_livestreams(livestreams_limit)
        num_all_streams = len(streams)
        streams, view_breakdowns = self.__filter_streams_by_views(streams, 4)
        num_filtered = num_all_streams - len(streams)
        self.reload_filter_logs()
        self.filterLogs.add_filter(num_all_streams, num_filtered, 4, view_breakdowns)
        self.filterLogs.export_to_csv()

        # loop over livestreams to access streamers
        # -> we can look up streamer profiles in bulk (batches of 100 IDs)
        #    so we want to break our livestreams into batches
        batch_num = 0
        batches = self.create_batches(streams, 100)
        for i in range(len(batches)):

            self.__print("BATCH " + str(i) + " / " + str(len(batches)))

            # get a list of all streamer_ids for this batch
            batch = batches[i]
            streamer_ids = []
            stream_lookup = {}
            for stream in batch:
                streamer_ids.append(stream.user_id)
                stream_lookup[stream.user_id] = stream

            # search for streamer objects and create a lookup table {streamer_id -> streamer object}
            # -> These have updated values, so we'll do our stream analysis on these and then call Streamers.update()
            for user in self.twitchAPI.get_streamers(streamer_ids):
                user_id = user['id']
                stream = stream_lookup[user_id]
                user['language'] = stream.language
                streamers.add_or_update_streamer(user)
                streamers.add_stream_data(stream_lookup[user_id])

        # record how many items were processed during the Twitch API's requests
        self.twitchAPI.request_logs.set_number_of_items(len(streams))

        if (self.mode == 'cli'):

            # log request stats
            print('\n\nRequest Logs')
            self.twitchAPI.request_logs.print_stats()
            num_streamers = len(streams)
            self.twitchAPI.request_logs.export_to_csv(self.filepaths['logs'], 'streamers', num_streamers)
            streamers.export_to_csv(self.filepaths['streamers'])

            # log a snapshot of the data
            self.insights.reload_data()
            insights = self.insights.get_snapshot_of_streamers_db()
            print('\n\nSnapshot of the Database:')
            for key, value in insights.items():
                print(key, "\n ->", value, "\n")
        return streamers


    # returns all livestreams up to a limit
    # -> uses a lookup table of already observed livestream IDs to make sure we know when to end
    def get_all_livestreams(self, limit = 9999999):

        self.__print('\nScraping Livestreams...')

        streams = []
        livestreams, cursor = self.twitchAPI.get_livestreams()
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

            self.__print('livestreams: ' + str(len(livestream_ids)))
            livestreams, cursor = self.twitchAPI.get_livestreams(cursor)
        return streams

    # filters streams to make sure only streams that have N or more viewers are included
    def __filter_streams_by_views(self, streams_list, filter_amount = 4):
        filtered_streams = []
        filtered_levels = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for stream in streams_list:
            if (stream.views >= filter_amount):
                filtered_streams.append(stream)

            if (stream.views >= 5):
                filtered_levels[5] += 1
            elif (stream.views == 4):
                filtered_levels[4] += 1
            elif (stream.views == 3):
                filtered_levels[3] += 1
            elif (stream.views == 2):
                filtered_levels[2] += 1
            elif (stream.views == 1):
                filtered_levels[1] += 1
            else:
                filtered_levels[0] += 1

        self.__print('Filtered out ' + str(len(streams_list) - len(filtered_streams)) + ' streams for having fewer than ' + str(filter_amount) + ' viewers')
        self.__print(str(len(filtered_streams)) + ' streams remain')
        self.__print(filtered_levels)
        return filtered_streams, filtered_levels


    # takes in a list of items l
    # returns a list of n batch_sized lists with items distributed into batches
    # ex: given l=[1, 2, 3, 4, 5] and batch_size=2
    #    -> [ [1, 2], [3, 4], [5] ]
    def create_batches(self, l, batch_size):
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


    # Scrape Videos ------------------------------------------------------------

    # .compile_streamers_db() doesn't add video data to streamer profiles because that would take too long
    # -> this function opens up the streamers DB and adds video data for streamers who are missing it
    # -> user can specify the number of streamers that get videos added in this execution
    def add_videos_to_streamers_db(self, streamers = False, video_limit = 9999999, streamer_limit = 9999999):

        if (streamers == False):
            streamers = Streamers(self.filepaths['streamers'], self.filepaths['streamers_missing_videos'])
        streamer_ids = streamers.get_ids_that_need_video_data()

        if (len(streamer_ids) == 0):
            return

        streamers_to_scrape = streamer_limit if (len(streamer_ids) > streamer_limit) else len(streamer_ids)
        self.__print('scraping videos for ' + str(streamers_to_scrape) + ' streamers (out of ' + str(len(streamer_ids)) + ' possible)')
        self.__print(str(len(streamers.known_missing_videos.get_ids())) + ' streamers have been removed because they appeared in streamers_missing_videos.csv')

        for i in range(streamers_to_scrape):
            streamer_id = streamer_ids[i]
            videos = self.get_all_videos_for_streamer(streamer_id, video_limit)
            self.__print(str(i) + ': streamer=' + str(streamer_id) + ', #videos=' + str(len(videos)))

            if (len(videos) == 0):
                streamers.add_streamer_to_missing_videos_collection(streamer_id)
            else:
                for video in videos:
                    streamers.add_stream_data(video)


        # record how many items were processed during this interaction
        self.twitchAPI.request_logs.set_number_of_items(streamers_to_scrape)

        if (self.mode == 'cli'):

            # save logs
            self.twitchAPI.request_logs.print_stats()
            self.twitchAPI.request_logs.export_to_csv(self.filepaths['logs'], 'videos', streamers_to_scrape)

            # save streamers object
            streamers.export_to_csv(self.filepaths['streamers'])

            # save missing video data
            streamers.known_missing_videos.export_to_csv(self.filepaths['streamers_missing_videos'])
        return streamers




    def get_all_videos_for_streamer(self, streamer_id, limit = 9999999):
        all_videos = []
        videos, cursor = self.twitchAPI.get_videos(streamer_id, False, limit)
        while ((len(videos) > 0) and (len(all_videos) < limit)):
            for video in videos:
                if (len(all_videos) < limit):
                    all_videos.append(Stream(video, False))

            quantity_to_request = limit - len(all_videos)
            videos, cursor = self.twitchAPI.get_videos(streamer_id, cursor, quantity_to_request)
        return all_videos



    # Scrape Follower Counts ---------------------------------------------------

    # loads all the streamers from the streamers.csv file and searches for follower data for them
    def add_followers_to_streamers_db(self, streamers = False, limit = 9999999):

        if (streamers == False):
            streamers = Streamers(self.filepaths['streamers'], self.filepaths['streamers_missing_videos'])
        streamer_ids = streamers.get_ids_with_missing_follower_data()

        # we can't add followers if there are no streamer profiles to add to
        if (len(streamer_ids) == 0):
            return streamers

        # get the number of streamers we will be processing
        num_streamers_to_process = limit if (limit < len(streamer_ids)) else len(streamer_ids)
        self.__print("scraping followers for " + str(num_streamers_to_process) + " streamers (out of " + str(len(streamer_ids)) + " possible)")

        # iterate over each streamer object and add a followers count to their profile
        for i in range(num_streamers_to_process):
            streamer_id = streamer_ids[i]
            self.__print(str(i) + ': ' + str(streamer_ids[i]))
            num_followers = self.twitchAPI.get_followers(streamer_id)
            streamers.add_follower_data(streamer_id, num_followers)

        # record how many items were processed during this interaction
        self.twitchAPI.request_logs.set_number_of_items(num_streamers_to_process)

        # save our results
        if (self.mode == 'cli'):
            self.twitchAPI.request_logs.print_stats()
            self.twitchAPI.request_logs.export_to_csv(self.filepaths['logs'], 'followers', num_streamers_to_process)
            streamers.export_to_csv(self.filepaths['streamers'])

        return streamers



# ==============================================================================
# RUN
# ==============================================================================

# Run the main scraper
def run():

    # get secret API clientIDs
    credentials = open('credentials.json')
    scraper = Scraper(json.load(credentials))

    # declare CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--games', dest='games', action="store_true", help='scrapes games from IGDB into /data/games.csv')
    parser.add_argument('-s', '--streamers', dest='streamers', action="store_true", help='scrapes all livestreams from Twitch and compiles corresponding streamer profiles into /data/streamers.csv')
    parser.add_argument('-v', '--videos', dest='videos', type=int, const=-1, nargs='?', help='scrapes video data for the N most popular streamers in the dataset that do not already have video data. If N missing, scrapes for all applicable streamers in dataset.')
    parser.add_argument('-f', '--followers', dest='followers', type=int, const=9999999, nargs='?', help='scrapes follower counts for the N most popular streamers in dataset that have not already had their follower count been recorded within the last 24 hours. If N missing, scrapes all applicable streamers in dataset.')
    args = parser.parse_args()

    # perform actions !
    if args.games:
        scraper.compile_games_db()
    if args.streamers:
        scraper.compile_streamers_db()
    if args.videos:
        if (args.videos == -1):
            scraper.add_videos_to_streamers_db()
        else:
            scraper.add_videos_to_streamers_db(False, 9999999, args.videos)
    if args.followers:
        scraper.add_followers_to_streamers_db(False, args.followers)



# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
