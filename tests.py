# ==============================================================================
# About
# ==============================================================================
#
# tests.py contains functions for testing the various components of scraper.py
#

import sys
import json

import scraper
from scraper import *

# ==============================================================================
# Test TwitchAPI
# ==============================================================================

# main function for testing the TwitchAPI class
def test_twitch_api(clientID):

    twitchAPI = TwitchAPI(clientID)
    test_names = [
        'games0', 'games1', 'games2', 'games3',
        'streamers0', 'streamers1', 'streamers2', 'streamers3',
        'followers0', 'followers1',
        'livestreams0', 'livestreams1', 'livestreams2',
        'videos0', 'videos1', 'videos2', 'videos3'
    ]
    tests = get_empty_test(test_names)

    # values to test with
    streamer_ids = ['39276140', '17337557']   # -> streamerIDs are for "Rubius" and "DrDisrespect"
    game_ids = ['493057', '515448']           # -> gameIDs for [PUBG, Resident Evil 3]


    # games test: 0 -> an individual game with a valid gameID
    games = twitchAPI.get_games(game_ids[1])
    if (games[0]['name'] != "Resident Evil 3"):
        tests['games0'] = False

    # games test: 1 -> an individual game with an invalid gameID
    games = twitchAPI.get_games("-1")
    if (len(games) != 0):
        tests['games1'] = False

    # games test: 2 -> input of a list of all valid games
    games = twitchAPI.get_games(game_ids)
    if (len(games) != len(game_ids)):
        tests['games2'] = False

    # games test: 3 -> input a list of games where 1 game has an invalid gameID
    games = twitchAPI.get_games([game_ids[0], "-1"])
    if (len(games) != 1):
        tests['games3'] = False


    # streamers test 0: -> an individual streamer with a valid ID
    streamers = twitchAPI.get_streamers(streamer_ids[0])
    if (streamers[0]['id'] != streamer_ids[0]):
        tests['streamers0'] = False

    # streamers test 1: -> an individual streamer with an invalid ID
    streamers = twitchAPI.get_streamers("-1")
    if (len(streamers) != 0):
        tests['streamers1'] = False


    # streamers test 3: -> input a list of streamers, all with valid IDs
    streamers = twitchAPI.get_streamers(streamer_ids)
    if (len(streamers) != len(streamer_ids)):
        tests['streamers2'] = False

    # streamers test 4: -> input a list of streamers with 1 invalid ID
    streamers = twitchAPI.get_streamers([streamer_ids[0], '-1'])
    if (len(streamers) != 0):
        tests['streamers3'] = False

    # followers test 1: -> input a valid streamer
    followers = twitchAPI.get_followers(streamer_ids[0])
    if (followers <= 0):
        tets['followers1'] = False

    # followers test 2: -> input an invalid streamer
    # note: for some reason, the Twitch API allows you to call negative streamer IDs
    #       and returns 0 (returns 24 if -1). This is weird behavior
    followers = twitchAPI.get_followers("sdflkdsf")
    if (followers >= 0):
        tests['followers2'] = False


    # livestreams test 0: -> no parameters (should get the top livestreams on Twitch right now)
    livestreams, cursor = twitchAPI.get_livestreams()
    if (len(livestreams) < 95):
        tests['livestreams0'] = False

    # livestreams test 1: -> use the token provided by livestreams call to get the next page of livestreams
    livestreams, cursor = twitchAPI.get_livestreams(cursor)
    if (len(livestreams) < 95):
        tests['livestreams1'] = False

    # livestreams test 2: -> using an invalid token
    # note: expected behavior is to ignore the invalid token entirely
    livestreams, cursor = twitchAPI.get_livestreams("invalid")
    if (len(livestreams) < 95):
        tests['livestreams2'] = False


    # videos test 0: -> get videos for a valid streamer
    videos, cursor = twitchAPI.get_videos(streamer_ids[0])
    if (len(videos) < 5):
        tests['videos0'] = False

    # videos test 1: -> get a limited number of videos from streamer
    videos, cursor = twitchAPI.get_videos(streamer_ids[0], False, 10)
    if (len(videos) < 1 or len(videos) > 10):
        tests['videos1'] = False

    # videos test 2: -> use cursor from videos test 1 to grab more streamer videos
    videos, cursor = twitchAPI.get_videos(streamer_ids[0], cursor)
    if (len(videos) < 1):
        tests['videos2'] = False

    # videos test 3: -> use cursor from videos test 2 to check what happens when you reach the end
    videos, cursor = twitchAPI.get_videos(streamer_ids[0], cursor)
    if (cursor != False or len(videos) != 0):
        tests['videos3'] = False


    print_test_results("TwitchAPI", tests)


# ==============================================================================
# Test IGDB API
# ==============================================================================


# main function for testing the TwitchAPI class
def test_igdb_api(clientID):

    igdbAPI = IGDBAPI(clientID)
    test_names = [
        'games_by_name0', 'games_by_name1', 'games_by_name2', 'games_by_name3',
        'games_by_offset0', 'games_by_offset'
    ]
    tests = get_empty_test(test_names)

    # values to test with
    game_names = ["halo"]
    invalid_game_names = ["ldskfjlkdsjflksdjf"]

    # games_by_name test 0: -> search for an individual game
    games = igdbAPI.search_for_game_by_name(game_names[0])
    if (not isinstance(games, dict)):
        tests['games_by_name0'] = False

    # games_by_name test 1: -> search for an invalid game
    games = igdbAPI.search_for_game_by_name(invalid_game_names[0])
    if (games != False):
        tests['games_by_name1'] = False

    # games_by_name test 2: -> search for all games that fit search parameter
    games = igdbAPI.search_for_game_by_name(game_names[0], True)
    if ((not isinstance(games, list)) or (len(games) < 1)):
        tests['games_by_name2'] = False

    # games_by_name test 3: -> search for list of games, but given an invalid game name
    games = igdbAPI.search_for_game_by_name(invalid_game_names[0], True)
    if ((not isinstance(games, list)) or (len(games) > 0)):
        tests['games_by_name3'] = False

    # games_by_offset test 0: -> test w/ default offset
    games = igdbAPI.search_for_games()
    if ((len(games) != 100) or (games[0]['id'] != 1)):
        tests['games_by_offset0'] = False

    # games_by_offset test 1: -> test w/ 100 offset
    games = igdbAPI.search_for_games(100)
    if ((len(games) != 100) or (games[0]['id'] != 101)):
        print(games[0]['id'])
        tests['games_by_offset1'] = False

    print_test_results("IGDB API", tests)


# ==============================================================================
# Test Compiling Games DB
# ==============================================================================


def test_complile_games_db(clientID):
    return
    scraper.compile_games_db(clientID)

# ==============================================================================
# Main Functions
# ==============================================================================

# Helper Functions -------------------------------------------------------------

# prints out the results of a suite of tests
def print_test_results(title, tests):
    print("------------------------------")
    print("Tests: ", title)
    print("------------------------------")
    correct = 0
    n = 0
    for key, value in tests.items():
        n += 1
        if (value == True):
            correct += 1
            print(" o <- ", key)
        else:
            print(" X <- ", key)

    print("-")
    print("Results: ", correct, "/", n, "(", round(correct / n * 100, 1), "%) correct")
    print("")

# given a list of names of tests, returns a dict with all {test_name: True}
def get_empty_test(test_names):
    test = {}
    for name in test_names:
        test[name] = True
    return test

# Main -------------------------------------------------------------------------

# Runs all tests
def main():


    # get secret API clientIDs
    credentials = open('credentials.json')
    credentials = json.load(credentials)

    # declare what tests to run - reference if statements below for test codes to add
    # -> if this list is empty, run all tests
    testing = []

    # tests!
    if ((len(testing) == 0) or ("Twitch API" in testing)):
        test_twitch_api(credentials['twitch'])
    if ((len(testing) == 0) or ("IGDB API" in testing)):
        test_igdb_api(credentials['igdb'])
    if ((len(testing) == 0) or ("Compile Games DB" in testing)):
        test_complile_games_db(credentials['igdb'])


# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main()
