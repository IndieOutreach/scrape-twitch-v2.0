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
def test_twitch_api(credentials):

    print_test_title("TwitchAPI")
    twitchAPI = TwitchAPI(credentials['twitch'])
    test_names = [
        'games0', 'games1', 'games2', 'games3',
        'streamers0', 'streamers1', 'streamers2', 'streamers3',
        'followers0', 'followers1', 'followers2',
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
    if (streamers[0]['id'] != int(streamer_ids[0])):
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

    # followers test 0: -> input a valid streamer
    followers = twitchAPI.get_followers(streamer_ids[0])
    if (followers <= 0):
        tets['followers0'] = False

    # followers test 1: -> input an invalid streamer
    # note: for some reason, the Twitch API allows you to call negative streamer IDs
    #       and returns 0 (returns 24 if -1). This is weird behavior
    followers = twitchAPI.get_followers("sdflkdsf")
    if (followers >= 0):
        tests['followers1'] = False

    # followers test 2: -> make sure that calling .get_streamers() includes an empty follower count list
    streamers = twitchAPI.get_streamers(streamer_ids)
    if ((len(streamers) < 0) or ('follower_counts' not in streamers[0]) or (not isinstance(streamers[0]['follower_counts'], list))):
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


    print_test_results(tests)


# ==============================================================================
# Test IGDB API
# ==============================================================================


# main function for testing the TwitchAPI class
def test_igdb_api(credentials):

    print_test_title("IGDB API")
    igdbAPI = IGDBAPI(credentials['igdb'])
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

    print_test_results(tests)


# ==============================================================================
# Test Compiling Games DB
# ==============================================================================


def test_complile_games_db(credentials):

    print_test_title("Compile Games DB")
    test_names = [
        'compile0', 'compile1',
        'data0', 'data1',
        'load0'
    ]
    tests = get_empty_test(test_names)
    known_missing_indexes = [165, 315, 577, 579, 580, 581]
    scraper = Scraper(credentials)
    scraper.set_mode('testing')
    scraper.set_print_mode(False)
    filename = './test/games.csv'
    wipe_file(filename)

    # compile test 0: -> scrape 500 Games
    games = scraper.compile_games_db(500)
    game_ids = games.get_ids()
    if (len(game_ids) != 500):
        tests['compile0'] = False
    else:
        for i in range(1, 503):
            if ((i not in game_ids) and (i not in known_missing_indexes)):
                tests['compile0'] = False

    # compile test 1: -> scrape 200 games
    games = scraper.compile_games_db(1000)
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
    games = scraper.compile_games_db(1500)
    game = games.get(740) # <- this should be Halo
    if ((game == False) or (not validate_game(game, 740, "Halo: Combat Evolved"))):
        tests['data1'] = False


    # load test 0: -> save data to .CSV, load it back into memory, and check if its the same
    games.export_to_csv(filename)
    new_games = Games(filename)
    if (not games.check_if_game_collections_same(new_games)):
        tests['load0'] = False
    elif (not validate_game(games.get(740), 740, "Halo: Combat Evolved")):
        tests['load0'] = False


    print_test_results(tests)


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

# Unfortunately, scraping streamers is a very time intensive process because it involves scraping videos
# therefore, these tests utilize small number of streamers
def test_scrape_streamers(credentials):

    print_test_title("Scrape Streamers")
    test_names = [
        'twitch0',
        'compile0',
        'load0'
    ]
    tests = get_empty_test(test_names)

    scraper = Scraper(credentials)
    scraper.set_mode('testing')
    scraper.set_print_mode(False)

    filename = './test/streamers.csv'
    wipe_file(filename)

    # twitch test 0: -> make sure that scraper.py can scrape all livestreams on Twitch
    #  - make sure that the function executes properly (average number of concurrent livestreams is < 200k)
    #twitchAPI = TwitchAPI(twitch_credentials)
    #if (len(scraper.get_all_livestreams(twitchAPI)) > 250000):
    #        tests['twitch0'] = False

    # compile test 0: -> make sure scraped streamers have games data
    streamers = scraper.compile_streamers_db(5)
    streamer_ids = streamers.get_streamer_ids()
    if (len(streamer_ids) == 0):
        tests['compile0'] = False
    else:
        streamer = streamers.get(streamer_ids[0])
        if (streamer == False):
            tests['compile0'] = False
        elif (streamer.stream_history == {}):
            tests['compile0'] = False
        elif (not validate_streamer(streamer)):
            tests['compile0'] = False


    # load 0: -> save the streamers to a CSV file and re-load it to make sure saving/loading works
    streamers.export_to_csv(filename)
    new_streamers = Streamers(filename)
    if (not streamers.check_if_streamer_collection_same(new_streamers)):
        tests['load0'] = False

    print_test_results(tests)


# returns true if streamer has all the right attributes to have been scraped correctly
# -> checks format of Streamer class object
def validate_streamer(streamer):
    if (streamer == False):
        return False

    streamer = streamer.to_dict()
    if (
        (streamer['id'] <= 0)                                                 or
        (len(streamer['login']) <= 0)                                         or
        (len(streamer['display_name']) <= 0)                                  or
        ('https://static-cdn.jtvnw.net' not in streamer['profile_image_url']) or
        (not validate_total_views(streamer['total_views']))                   or
        (not isinstance(streamer['follower_counts'], list))                   or
        (streamer['language'] == '')                                          or
        (not validate_stream_history(streamer['stream_history']))
        ):
        return False
    return True

# makes sure that stream history is correctly formatted and streamer has some views
def validate_stream_history(stream_history):
    for game_key in stream_history:
        game = stream_history[game_key]
        if (
            (('views' not in game) or (not isinstance(game['views'], int)))   or
            (('videos' not in game) or (not isinstance(game['videos'], int))) or
            (('dates' not in game) or (len(game['dates']) <= 0))
            ):
            return False
    return True

# makes sure that a total_views object is correctly formatted and has some view counts
def validate_total_views(total_views):
    if ((not (isinstance(total_views, list)) or (len(total_views) == 0))):
        return False

    for obj in total_views:
        if (
            (('views' not in obj) or (obj['views'] <= 0)) or
            (('date' not in obj) or (obj['date'] <= 0))
            ):
            return False
    return True

# ==============================================================================
# Test TimeLogs
# ==============================================================================

# test to see if timelogs work in TwitchAPI
def test_timelogs(credentials):

    print_test_title("TimeLogs")

    test_names = [
        'init0', 'init1',
        'run0', 'run1', 'run2',
        'save0'
    ]
    tests = get_empty_test(test_names)

    twitchAPI = TwitchAPI(credentials['twitch'])
    test_csv_file = './test/runtime.csv'
    wipe_file(test_csv_file)

    # initialize 0: -> make sure logs are initialized to be empty
    for key, value in twitchAPI.request_logs.logs.items():
        if (len(value) > 0):
            tests['init0'] = False

    # init 1: -> make sure action categories are correct
    twitch_actions = ['get_livestreams', 'get_streamers', 'get_videos', 'get_game_name_in_video', 'get_followers', 'get_games']
    for key in twitchAPI.request_logs.logs:
        if (key not in twitch_actions):
            tests['init1'] = False

    # run 0: -> see if number of actions increases after executing
    livestreams, cursor = twitchAPI.get_livestreams()
    if (len(twitchAPI.request_logs.logs['get_livestreams']) == 0):
        tests['run0'] = False

    # run 1: -> see if running get_livestreams() again increases # of livestreams
    times_run = len(twitchAPI.request_logs.logs['get_livestreams'])
    livestreams, cursor = twitchAPI.get_livestreams(cursor)
    livestreams, cursor = twitchAPI.get_livestreams(cursor)
    if (len(twitchAPI.request_logs.logs['get_livestreams']) <= times_run):
        print(twitchAPI.request_logs.logs)
        tests['run1'] = False

    # run 2: -> make sure that each action has an end time
    for action in twitchAPI.request_logs.logs['get_livestreams']:
        if (action['start'] > action['end']):
            tests['run2'] = False

    # save 0: -> save to CSV file
    twitchAPI.request_logs.export_to_csv(test_csv_file, 'test1', len(livestreams))
    content = twitchAPI.request_logs.load_from_csv(test_csv_file)
    if (len(content) == 0):
        tests['save0'] = False
    else:
        old_length = len(content)
        twitchAPI.get_livestreams()
        twitchAPI.request_logs.export_to_csv(test_csv_file, 'test2', len(livestreams))
        content = twitchAPI.request_logs.load_from_csv(test_csv_file)
        if (len(content) <= old_length):
            tests['save0'] = False


    print_test_results(tests)

# ==============================================================================
# Test Add Followers
# ==============================================================================

def test_add_followers(credentials):

    print_test_title("Add Followers")
    test_names = [
        'followers0'
    ]
    tests = get_empty_test(test_names)

    scraper = Scraper(credentials)
    scraper.set_mode('testing')
    scraper.set_print_mode(False)

    filename = './test/streamers.csv'
    wipe_file(filename)

    # followers0: -> make sure that a streamer's follower_counts increases
    # Because .add_followers_to_streamers_db() *needs* a filepath, we will create a .csv file for it to load
    streamers1 = scraper.compile_streamers_db(5)
    streamers1.export_to_csv(filename)
    streamers2 = scraper.add_followers_to_streamers_db(filename)

    for id in streamers1.get_streamer_ids():
        if (id not in streamers2.get_streamer_ids()):
            tests['followers0'] = False

        streamer1 = streamers1.get(id)
        streamer2 = streamers2.get(id)

        if (len(streamer2.follower_counts) <= len(streamer1.follower_counts)):
            tests['followers0'] = False
        elif (not validate_follower_counts(streamer2.follower_counts)):
            tests['followers0'] = False


    print_test_results(tests)


# makes sure follower_counts has format:
# - [{'followers': INT, 'date': INT_DATE}]
def validate_follower_counts(counts):
    for obj in counts:
        if (not isinstance(obj, dict)):
            return False
        if (('followers' not in obj) or (not isinstance(obj['followers'], int))):
            return False
        if (('date' not in obj) or (obj['date'] <= 0)):
            return False

    return True

# ==============================================================================
# Test Add Videos
# ==============================================================================

def test_add_videos(credentials):
    print_test_title("Add Videos")
    test_names = [
        'videos0', 'videos1'
    ]
    tests = get_empty_test(test_names)

    scraper = Scraper(credentials)
    scraper.set_mode('testing')
    scraper.set_print_mode(False)
    
    filename = './test/streamers_videos.csv'
    wipe_file(filename)

    # videos0: -> scrape videos and check streamer objects
    streamers1 = scraper.compile_streamers_db(5)
    streamers1.export_to_csv(filename)
    streamers2 = scraper.add_videos_to_streamers_db(filename, 15)
    num_streamers_without_videos = 0
    for streamer_id in streamers1.get_streamer_ids():
        streamer1 = streamers1.get(streamer_id)
        streamer2 = streamers2.get(streamer_id)

        if (len(streamer2.stream_history) <= len(streamer1.stream_history)):
            num_streamers_without_videos += 1

    if (num_streamers_without_videos >= 5):
        tests['videos0'] = False

    # videos1: -> make sure scraping videos decreases the number of streamers eligible to have their videos scraped
    old_amount = len(streamers1.get_streamers_ids_with_no_video_data())
    new_amount = len(streamers2.get_streamers_ids_with_no_video_data())
    if (new_amount >= old_amount):
        tests['videos1'] = False

    print_test_results(tests)


# ==============================================================================
# Main Functions
# ==============================================================================

# Helper Functions -------------------------------------------------------------

def print_test_title(title):
    print("==============================")
    print("Tests: ", title)
    print("==============================")


# prints out the results of a suite of tests
def print_test_results( tests):

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

# overwrites any existing file at filename
# -> use this at the beginning of each test to make sure no other data interferes
def wipe_file(filename):
    s = Streamers()
    s.export_to_csv(filename)
    return


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
        test_twitch_api(credentials)
    if ((len(testing) == 0) or ("IGDB API" in testing)):
        test_igdb_api(credentials)
    if ((len(testing) == 0) or ("Compile Games DB" in testing)):
        test_complile_games_db(credentials)
    if ((len(testing) == 0) or ("Compile Streamers DB" in testing)):
        test_scrape_streamers(credentials)
    if ((len(testing) == 0) or ("TimeLogs" in testing)):
        test_timelogs(credentials)
    if ((len(testing) == 0) or ("Add Followers" in testing)):
        test_add_followers(credentials)
    if ((len(testing) == 0) or ("Add Videos" in testing)):
        test_add_videos(credentials)


# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main()
