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
from games import *
from streamers import *

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
        'videos0', 'videos1', 'videos2', 'videos3', 'videos4'
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

    # videos test 1: -> check to see if game name in video results
    # -> validating that TwitchAPI.get_videos() successfully calls .get_game_name_in_video() and attaches to video object
    game_found = False
    for video in videos:
        if (video['game_name'] != ""):
            game_found = True
    if (not game_found):
        tests['videos1'] = False

    # videos test 2: -> get a limited number of videos from streamer
    videos, cursor = twitchAPI.get_videos(streamer_ids[0], False, 10)
    if (len(videos) < 1 or len(videos) > 10):
        tests['videos2'] = False

    # videos test 3: -> use cursor from videos test 1 to grab more streamer videos
    videos, cursor = twitchAPI.get_videos(streamer_ids[0], cursor)
    if (len(videos) < 1):
        tests['videos3'] = False

    # videos test 4: -> use cursor from videos test 2 to check what happens when you reach the end
    videos, cursor = twitchAPI.get_videos(streamer_ids[0], cursor)
    if (cursor != False or len(videos) != 0):
        tests['videos4'] = False


    print_test_results("TwitchAPI", tests)


# ==============================================================================
# Test IGDB API
# ==============================================================================


# main function for testing the TwitchAPI class
def test_igdb_api(clientID):

    igdbAPI = IGDBAPI(clientID)
    test_names = [
        'games_by_name0', 'games_by_name1', 'games_by_name2', 'games_by_name3',
        'games_by_offset0', 'games_by_offset1',
        'game_covers0', 'game_covers1', 'game_covers2', 'game_covers3', 'game_covers4'
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
    games, offset = igdbAPI.search_for_games()
    if ((len(games) != 500) or (offset != 500) or (games[0]['id'] != 1)):
        tests['games_by_offset0'] = False

    # games_by_offset test 1: -> test w/ 100 offset
    games, offset = igdbAPI.search_for_games(500)
    if ((len(games) != 500) or (offset != 1000) or (games[0]['id'] != 501)):
        tests['games_by_offset1'] = False

    # game_covers test 0: -> test w/ default offset
    covers = igdbAPI.search_for_game_covers()
    if ((len(covers) != 125) or (not isinstance(covers, dict))):
        tests['game_covers0'] = False

    # game_covers test 1: -> test offset
    min, max = (100000000, -1)
    covers = igdbAPI.search_for_game_covers(100)
    for game_id in covers:
        max = game_id if (game_id > max) else max
        min = game_id if (game_id < min) else min
    if ((min != 101) or (max != 225)):
        tests['game_covers1'] = False


    # game_covers 2: -> make sure that games in .search_for_games() have a 'igdb_box_art_url'
    games, offset = igdbAPI.search_for_games()
    if (('igdb_box_art_url' not in games[0]) or ('images.igdb.com' not in games[0]['igdb_box_art_url'])):
        tests['game_covers2'] = False


    # game_covers 3: -> make sure that games in .search_for_game_by_name() have 'igdb_box_art_url'
    game = igdbAPI.search_for_game_by_name(game_names[0])
    if (('igdb_box_art_url' not in game) or ('images.igdb.com' not in game['igdb_box_art_url'])):
        tests['game_covers3'] = False

    # games_covers4: -> make sure that all games in results for .search_for_game_by_name() get 'igdb_box_art_url's
    games = igdbAPI.search_for_game_by_name(game_names[0], True)
    for game in games:
        if (('igdb_box_art_url' not in game) or ('images.igdb.com' not in game['igdb_box_art_url'])):
            tests['game_covers4'] = False

    print_test_results("IGDB API", tests)


# ==============================================================================
# Test Compiling Games DB
# ==============================================================================


def test_complile_games_db(clientID):

    test_names = [
        'compile0', 'compile1',
        'data0', 'data1',
        'load0'
    ]
    tests = get_empty_test(test_names)
    known_missing_indexes = [165, 315, 577, 579, 580, 581]

    # compile test 0: -> scrape 500 Games
    games = scraper.compile_games_db(clientID, 500)
    game_ids = games.get_ids()
    if (len(game_ids) != 500):
        tests['compile0'] = False
    else:
        for i in range(1, 503):
            if ((i not in game_ids) and (i not in known_missing_indexes)):
                tests['compile0'] = False

    # compile test 1: -> scrape 200 games
    games = scraper.compile_games_db(clientID, 1000)
    game_ids = games.get_ids()
    if (len(game_ids) < 990):
        tests['compile1'] = False
    else:
        for i in range(1, 1000):
            if ((i not in game_ids) and (i not in known_missing_indexes)):
                tests['compile1'] = False


    # data test 0: -> make sure data within a game is actually what we are expecting
    game = games.get(1) # <- this should be Thief
    if ((game == False) or (not validate_game(game, 1, "Thief II: The Metal Age"))):
        tests['data0'] = False

    # data test 1: -> make sure data within a different game is actually what we are expecting
    games = scraper.compile_games_db(clientID, 1500)
    game = games.get(740) # <- this should be Halo
    if ((game == False) or (not validate_game(game, 740, "Halo: Combat Evolved"))):
        tests['data1'] = False


    # load test 0: -> save data to .CSV, load it back into memory, and check if its the same
    games.export_to_csv('./test_csv_output/games.csv')
    new_games = Games('./test_csv_output/games.csv')
    if (not games.check_if_game_collections_same(new_games)):
        tests['data0'] = False
    elif (not validate_game(games.get(740), 740, "Halo: Combat Evolved")):
        tests['data0'] = False


    print_test_results("Compile Games DB", tests)


# makes sure that a Game has the right types on its attributes
def validate_game(game, expected_game_id, expected_title):
    if (game == False):
        return False

    game_obj = game.to_dict()
    if (
        (game_obj['id'] != expected_game_id)                       or
        (game_obj['name'] != expected_title)                       or
        (not validate_igdb_array(game_obj, "genres"))              or
        (not validate_igdb_array(game_obj, "keywords"))            or
        (not validate_igdb_array(game_obj, "themes"))              or
        (not validate_igdb_array(game_obj, "platforms"))           or
        (not validate_igdb_array(game_obj, "player_perspectives")) or
        (not validate_igdb_array(game_obj, "similar_games"))       or
        (not validate_igdb_array(game_obj, "age_ratings"))         or
        (not validate_igdb_array(game_obj, "game_modes"))          or
        (not isinstance(game_obj['category'], int))                or
        (not isinstance(game_obj['release_date'], int))            or
        (not isinstance(game_obj['popularity'], float))            or
        (not isinstance(game_obj['collection'], int))              or
        (not isinstance(game_obj['time_to_beat'], int))            or
        ((not isinstance(game_obj['igdb_box_art_url'], str)))      or
        (('images.igdb.com' not in game_obj['igdb_box_art_url']))  or
        (not isinstance(game_obj['twitch_box_art_url'], str))
        ):
        return False
    return True

# takes in an Array of integer IDs from a game Object
# returns True if the format is correct
def validate_igdb_array(game_obj, list_name):
    if (list_name not in game_obj):
        return False
    list_obj = game_obj[list_name]
    if (not isinstance(list_obj, list)):
        return False
    elif (len(list_obj) == 0):
        return False
    elif (not isinstance(list_obj[0], int)):
        return False
    return True


# ==============================================================================
# Test Scrape Streamers
# ==============================================================================


def test_scrape_streamers(twitch_credentials, igdb_credentials):

    #scraper.scrape_streamers(twitch_credentials)
    return

    twitchAPI = TwitchAPI(twitch_credentials)
    igdbAPI = IGDBAPI(igdb_credentials)

    test_names = [
        'compile0'
    ]
    tests = get_empty_test(test_names)



    print_test_results("Scrape Streamers", tests)

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
    if ((len(testing) == 0) or ("Scrape Streamers" in testing)):
        test_scrape_streamers(credentials['twitch'], credentials['igdb'])


# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main()
