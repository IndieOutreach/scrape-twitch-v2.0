# ==============================================================================
# About
# ==============================================================================
#
# insights.py is a script for drawing insights from our data:
# - games.csv
# - streamers.csv
#

import os
import sys
import math
import zipfile

from zipfile import *
from io import StringIO
from io import TextIOWrapper


from logs import *
from games import *
from streamers import *

# ==============================================================================
# Class: Insights
# ==============================================================================

class Insights():

    def __init__(self, dataset = False, month = False):
        month = datetime.datetime.now().strftime("%Y-%m") if (month == False) else month
        self.month = month
        if (dataset != False):
            self.set_dataset(dataset, month)
        else:
            self.mode = False
            self.streamers = False
            self.games = False
            self.streamerLogs = False
        self.logging_mode = False
        return

    # loads datasets
    def set_dataset(self, mode, month):
        if (mode == 'cli'):
            self.mode = 'cli'
            self.streamers = Streamers('./data/streamers', './data/streamers_missing_videos.csv')
            self.games = Games('./data/games.csv')
            self.streamerslogs = GeneralLogs('./logs/streamer_insights[' + month + '].csv')
        elif (mode == 'testing'):
            self.mode = 'testing'
            self.streamers = Streamers('./test/streamers')
            self.games = Games('./test/games.csv')
            self.streamerslogs = GeneralLogs('./test/streamer_insights[' + month + '].csv')
        elif (mode == 'production'):
            self.mode = 'production'
            self.streamers = False
            self.games = False
            self.streamerslogs = GeneralLogs('./logs/streamer_insights[' + month + '].csv')

    def reload_data(self):
        self.set_dataset(self.mode)


    def set_logging(self, mode):
        self.logging_mode = mode

    # manually sets a specific type of data (instead of loading from filesystem)
    # for example, data_obj could be a Streamers() or Games() object
    def set_data(self, type, data_obj):
        if (type == 'streamers'):
            self.streamers = data_obj
        elif (type == 'games'):
            self.games = data_obj
        elif (type == 'streamerslogs'):
            self.streamerslogs = data_obj


    # when given a "YYYY-mm" date stamp, update filepaths to reflect this month
    def set_month(self, month):
        if (month == self.month):
            return
        self.month = month
        if ((self.mode == 'production') or (self.mode == 'cli')):
            self.streamerslogs = GeneralLogs('./logs/streamer_insights[' + month + '].csv')
        elif (self.mode == 'testing'):
            self.streamerslogs = GeneralLogs('./test/streamer_insights[ ' + month + '].csv')


    # Streamers: Scraping ------------------------------------------------------

    # This function is useful for spotting possible errors or irregularities in the scraping of the data
    # Questions this function answers
    # - How many streamers don't have videos?
    # - How many streamers don't have livestreams from the last day?
    # - How many streamers don't have a view count from the last day?
    # - How many streamers don't have a follower count from the last day?
    # - How many follower_count objects does a streamer typically have?
    # - What is the breakdown of languages used by streamers?
    # - What is the average number of games livestreamed? in videos?
    # - How much filespace does storing these streamers take?
    def get_snapshot_of_streamers_db(self):

        results = {
            'have_video_data': {'percentage': 0, 'number': 0},
            'zero_videos': {},
            'followers_past_day': {'percentage': 0, 'number': 0},
            'num_follower_counts': {},
            'num_view_counts': {},
            'livestreamed_past_day': {'percentage': 0, 'number': 0},
            'livestreamed_past_week': {'percentage': 0, 'number': 0},
            'has_view_data_past_day': {'percentage': 0, 'number': 0},
            'languages': {},
            'filespace': {}
        }

        # variables
        num_streamers = len(self.streamers.get_ids())
        if (num_streamers == 0):
            return results
        time_today = int(time.time())
        time_yesterday = time_today - (60*60*24) # <- seconds*minutes*hours
        time_week = time_today - (60*60*24*7)


        # Q: How many streamers don't have videos?
        num_no_video_ids = len(self.streamers.get_ids_with_no_video_data())
        results['have_video_data']['percentage'] = round(100 - (num_no_video_ids / num_streamers * 100), 2)
        results['have_video_data']['number']     = num_streamers - num_no_video_ids
        results['zero_videos']                   = self.get_stats_about_streamers_missing_videos()

        # Q: How many streamers don't have follower data from last day?
        num_no_followers = len(self.streamers.get_ids_with_missing_follower_data())
        results['followers_past_day']['number']     = num_streamers - num_no_followers
        results['followers_past_day']['percentage'] = round(100 - (num_no_followers / num_streamers * 100), 2)

        # Q: How many streamers livestreamed during the past day? past week?
        num_past_day = len(self.streamers.get_ids_who_livestreamed_in_range(time_yesterday, time_today))
        num_past_week = len(self.streamers.get_ids_who_livestreamed_in_range(time_week, time_today))
        results['livestreamed_past_day']['number']      = num_past_day
        results['livestreamed_past_day']['percentage']  = round(num_past_day / num_streamers * 100, 2)
        results['livestreamed_past_week']['number']     = num_past_week
        results['livestreamed_past_week']['percentage'] = round(num_past_week / num_streamers * 100, 2)

        # Q: How many streamers have view counts from the last day?
        num_view_counts = len(self.streamers.get_ids_with_view_counts_in_range(time_yesterday, time_today))
        results['has_view_data_past_day']['percentage'] = round(num_view_counts / num_streamers * 100, 2)
        results['has_view_data_past_day']['number']     = num_view_counts

        # Q: How many follower_count objects does a streamer typically have?
        # Q: How many view_count objects does a streamer typically have?
        # Q: What is the breakdown of languages in the dataset?
        for id in self.streamers.get_ids():
            streamer = self.streamers.get(id)
            num_objects = len(streamer.follower_counts)
            if (num_objects in results['num_follower_counts']):
                results['num_follower_counts'][num_objects] += 1
            else:
                results['num_follower_counts'][num_objects] = 1

            num_objects = len(streamer.view_counts)
            if (num_objects in results['num_view_counts']):
                results['num_view_counts'][num_objects] += 1
            else:
                results['num_view_counts'][num_objects] = 1

            if (streamer.language in results['languages']):
                results['languages'][streamer.language] += 1
            else:
                results['languages'][streamer.language] = 1


        # Q: What is the breakdown of stream_history values, as defined by .get_stream_history_stats()?
        stream_history_stats = self.get_stream_history_stats()
        for key, value in stream_history_stats.items():
            results[key] = value

        # Q: What is the number of views per stream like?
        results['views_per_stream'] = self.get_livestream_views_breakdown()

        # Q: What is the total number of streamers in dataset? videos? livestreams? games?
        results['totals'] = self.get_totals()

        # Q: How much filespace does storing the Streamers dataset take up?
        results['filespace'] = self.get_filesizes_for_streamers()

        # log this insight
        if (self.logging_mode == True):
            self.streamerslogs.add(results)
            self.streamerslogs.export_to_csv()
        return results




    # gets data about Streamer.stream_history values
    # - min, max, mean, median, std_dev number of livestreams a streamer has.
    # - min, max, mean, median, std_dev number of videos a streamer has. (of those with videos)
    # - min, max, mean, median, std_dev number of games a streamer has livestreamed
    # - min, max, mean, median, std_dev number of games a streamer has played in a video (of those with videos)
    def get_stream_history_stats(self):
        stats = {
            'livestreams_per_streamer': {'num_streamers': 0, 'min': -1, 'max': -1, 'mean': 0, 'median': 0, 'std_dev': 0},
            'games_per_streamer_from_livestreams': {'num_streamers': 0, 'min': -1, 'max': -1, 'mean': 0, 'median': 0, 'std_dev': 0},
            'videos_per_streamer': {'num_streamers': 0, 'min': -1, 'max': -1, 'mean': 0, 'median': 0, 'std_dev': 0},
            'games_per_streamer_from_videos': {'num_streamers': 0, 'min': -1, 'max': -1, 'mean': 0, 'median': 0, 'std_dev': 0}
        }


        median_lists = {
            'livestreams_per_streamer': [],
            'games_per_streamer_from_livestreams': [],
            'videos_per_streamer': [],
            'games_per_streamer_from_videos': []
        }

        # use this for caching values between first and second passes
        lookup = {
            'livestreams_per_streamer': {},
            'videos_per_streamer': {},
            'games_per_streamer_from_videos': {},
            'games_per_streamer_from_livestreams': {}
        }


        def add_min_max_data(stats_obj, key, val):
            if ((stats_obj[key]['min'] == -1) or (stats_obj[key]['min'] > val)):
                stats_obj[key]['min'] = val
            if ((stats_obj[key]['max'] == -1) or (stats_obj[key]['max'] < val)):
                stats_obj[key]['max'] = val
            return stats_obj


        # FIRST PASS: get data for calculating mean values
        for id in self.streamers.get_ids():

            streamer = self.streamers.get(id)
            livestreams, videos = streamer.get_games_played()
            lookup['games_per_streamer_from_videos'][id]      = len(videos) # <- use so we don't have to call .get_games_played() on second pass
            lookup['games_per_streamer_from_livestreams'][id] = len(livestreams)
            lookup['livestreams_per_streamer'][id]            = 0
            lookup['videos_per_streamer'][id]                 = 0
            old_num_videos      = stats['videos_per_streamer']['num_streamers'] # <- use these to make sure we don't double count streamer
            old_num_livestreams = stats['livestreams_per_streamer']['num_streamers']

            # 1) process quantity values and keep track of game info
            for game in streamer.stream_history:

                if (isinstance(game, int)): # <- This is for a Livestream
                    times_played = len(streamer.stream_history[game]['dates'])
                    if (stats['livestreams_per_streamer']['num_streamers'] == old_num_livestreams):
                        stats['livestreams_per_streamer']['num_streamers']       += 1
                        stats['games_per_streamer_from_livestreams']['num_streamers'] += 1

                    if (id in lookup['livestreams_per_streamer']):
                        lookup['livestreams_per_streamer'][id] += times_played
                    else:
                        lookup['livestreams_per_streamer'][id] = times_played


                else:                       # <- This is for a Video
                    times_played = len(streamer.stream_history[game]['dates'])
                    if (stats['videos_per_streamer']['num_streamers'] == old_num_videos):
                        stats['videos_per_streamer']['num_streamers']       += 1
                        stats['games_per_streamer_from_videos']['num_streamers'] += 1

                    if (id in lookup['videos_per_streamer']):
                        lookup['videos_per_streamer'][id] += times_played
                    else:
                        lookup['videos_per_streamer'][id] = times_played


            # 2) add quantity stats for the current streamer
            stats['livestreams_per_streamer']['mean'] += lookup['livestreams_per_streamer'][id]
            stats = add_min_max_data(stats, 'livestreams_per_streamer', lookup['livestreams_per_streamer'][id])

            if (lookup['videos_per_streamer'][id] > 0):
                stats['videos_per_streamer']['mean'] += lookup['videos_per_streamer'][id]
                stats = add_min_max_data(stats, 'videos_per_streamer', lookup['videos_per_streamer'][id])


            # 3) add game info to stats (for mean)
            stats['games_per_streamer_from_livestreams']['mean'] += lookup['games_per_streamer_from_livestreams'][id]
            stats = add_min_max_data(stats, 'games_per_streamer_from_livestreams', lookup['games_per_streamer_from_livestreams'][id])

            if (lookup['games_per_streamer_from_videos'][id] > 0):
                stats['games_per_streamer_from_videos']['mean'] += lookup['games_per_streamer_from_videos'][id]
                stats = add_min_max_data(stats, 'games_per_streamer_from_videos', lookup['games_per_streamer_from_videos'][id])


            # 4) Add data to median lists for streamer
            if (lookup['livestreams_per_streamer'][id] > 0):
                median_lists['livestreams_per_streamer'].append(lookup['livestreams_per_streamer'][id])
            if (lookup['videos_per_streamer'][id] > 0):
                median_lists['videos_per_streamer'].append(lookup['videos_per_streamer'][id])
            if (lookup['games_per_streamer_from_livestreams'][id] > 0):
                median_lists['games_per_streamer_from_livestreams'].append(lookup['games_per_streamer_from_livestreams'][id])
            if (lookup['games_per_streamer_from_videos'][id] > 0):
                median_lists['games_per_streamer_from_videos'].append(lookup['games_per_streamer_from_videos'][id])

        # calculate out the correct mean values
        if (stats['livestreams_per_streamer']['num_streamers'] > 0):
            stats['livestreams_per_streamer']['mean'] = stats['livestreams_per_streamer']['mean'] / stats['livestreams_per_streamer']['num_streamers']
        if (stats['games_per_streamer_from_livestreams']['num_streamers'] > 0):
            stats['games_per_streamer_from_livestreams']['mean'] = stats['games_per_streamer_from_livestreams']['mean'] / stats['games_per_streamer_from_livestreams']['num_streamers']
        if (stats['videos_per_streamer']['num_streamers'] > 0):
            stats['videos_per_streamer']['mean'] = stats['videos_per_streamer']['mean'] / stats['videos_per_streamer']['num_streamers']
        if (stats['games_per_streamer_from_videos']['num_streamers'] > 0):
            stats['games_per_streamer_from_videos']['mean'] = stats['games_per_streamer_from_videos']['mean'] / stats['games_per_streamer_from_videos']['num_streamers']

        # calculate medians
        for key in median_lists:
            median_lists[key].sort()
            midpoint = int(len(median_lists[key]) / 2)
            if (midpoint < len(median_lists[key])):
                stats[key]['median'] = median_lists[key][midpoint]


        # SECOND PASS: calculate variance and std_deviation
        for id in self.streamers.get_ids():
            streamer = self.streamers.get(id)

            num_livestreams                         = lookup['livestreams_per_streamer'][id] if (id in lookup['livestreams_per_streamer']) else False
            num_games_per_streamer_from_livestreams = lookup['games_per_streamer_from_livestreams'][id] if (id in lookup['games_per_streamer_from_livestreams']) else False
            num_videos                              = lookup['videos_per_streamer'][id] if (id in lookup['videos_per_streamer']) else False
            num_games_per_streamer_from_videos      = lookup['games_per_streamer_from_videos'][id] if (id in lookup['games_per_streamer_from_videos']) else False

            # calculate variances using formula: var = SUM{ (mean - observed)^2 }
            if ((num_livestreams != False) and (num_livestreams > 0)):
                stats['livestreams_per_streamer']['std_dev'] += (stats['livestreams_per_streamer']['mean'] - num_livestreams) ** 2
            if ((num_games_per_streamer_from_livestreams != False) and (num_games_per_streamer_from_livestreams > 0)):
                stats['games_per_streamer_from_livestreams']['std_dev'] += (stats['games_per_streamer_from_livestreams']['mean'] - num_games_per_streamer_from_livestreams) ** 2
            if ((num_videos != False) and (num_videos > 0)):
                stats['videos_per_streamer']['std_dev'] += (stats['videos_per_streamer']['mean'] - num_videos) ** 2
            if ((num_games_per_streamer_from_videos != False) and (num_games_per_streamer_from_videos > 0)):
                stats['games_per_streamer_from_videos']['std_dev'] += (stats['games_per_streamer_from_videos']['mean'] - num_games_per_streamer_from_videos) ** 2



        # complete variance calculations using formula: var = var / (# of items in sample - 1)
        if (stats['livestreams_per_streamer']['num_streamers'] > 1):
            stats['livestreams_per_streamer']['std_dev'] = stats['livestreams_per_streamer']['std_dev'] / (stats['livestreams_per_streamer']['num_streamers'] - 1)
        if (stats['games_per_streamer_from_livestreams']['num_streamers'] > 1):
            stats['games_per_streamer_from_livestreams']['std_dev'] = stats['games_per_streamer_from_livestreams']['std_dev'] / (stats['games_per_streamer_from_livestreams']['num_streamers'] - 1)
        if (stats['videos_per_streamer']['num_streamers'] > 1):
            stats['videos_per_streamer']['std_dev'] = stats['videos_per_streamer']['std_dev'] / (stats['videos_per_streamer']['num_streamers'] - 1)
        if (stats['games_per_streamer_from_videos']['num_streamers'] > 1):
            stats['games_per_streamer_from_videos']['std_dev'] = stats['games_per_streamer_from_videos']['std_dev'] / (stats['games_per_streamer_from_videos']['num_streamers'] - 1)

        # convert variance into standard deviation by square rooting it
        stats['livestreams_per_streamer']['std_dev']            = math.sqrt(stats['livestreams_per_streamer']['std_dev'])
        stats['games_per_streamer_from_livestreams']['std_dev'] = math.sqrt(stats['games_per_streamer_from_livestreams']['std_dev'])
        stats['videos_per_streamer']['std_dev']                 = math.sqrt(stats['videos_per_streamer']['std_dev'])
        stats['games_per_streamer_from_videos']['std_dev']      = math.sqrt(stats['games_per_streamer_from_videos']['std_dev'])


        # round values
        for key in stats:
            stats[key]['mean']    = round(stats[key]['mean'], 2)
            stats[key]['std_dev'] = round(stats[key]['std_dev'], 2)

        return stats


    # returns a breakdown of the number of views each streamer has
    def get_livestream_views_breakdown(self):

        lookup = { 'views_per_stream': {}, 'views_per_stream_list': [] }
        stats = {
            'num_streamers': 0,
            'mean': 0,
            'median': 0,
            'std_dev': 0,
            'min': -1,
            'max': -1
        }

        # get total view counts (from livestreams) for every streamer
        for id in self.streamers.get_ids():
            streamer = self.streamers.get(id)
            livestream_history = streamer.get_livestream_history()
            lookup['views_per_stream'][id] = 0
            for game in livestream_history:
                lookup['views_per_stream'][id] += livestream_history[game]['views']
            lookup['views_per_stream'][id] = lookup['views_per_stream'][id] / len(livestream_history)
            lookup['views_per_stream_list'].append(lookup['views_per_stream'][id])

        # get the mean views and calculate min/max
        min, max = -1, -1
        mean = 0
        for streamer_id, views in lookup['views_per_stream'].items():
             mean += views

             # calculate min/max
             if ((min == -1) or (min > views)):
                 min = views
             if ((max == -1) or (max < views)):
                 max = views

        mean = mean / len(lookup['views_per_stream'])

        # get the variance -> standard deviation
        std_dev = 0
        for streamer_id, views in lookup['views_per_stream'].items():
            std_dev += (mean - views) ** 2
        if (len(lookup['views_per_stream']) > 1):
            std_dev = std_dev / (len(lookup['views_per_stream']) - 1)
        std_dev = math.sqrt(std_dev)

        # calculate median
        lookup['views_per_stream_list'].sort()
        midpoint = int(len(lookup['views_per_stream_list']) / 2)
        median = lookup['views_per_stream_list'][midpoint]

        # return stats object
        stats['num_streamers'] = len(lookup['views_per_stream'])
        stats['mean']    = round(mean, 2)
        stats['median']  = median
        stats['std_dev'] = round(std_dev, 2)
        stats['min']     = min
        stats['max']     = max
        return stats


    # returns the total number of videos, livestreams etc in the dataset
    def get_totals(self):

        stats = {'num_streamers': 0, 'num_livestreams': 0, 'num_videos': 0, 'games_from_livestreams': 0, 'games_from_videos': 0}
        stats['num_streamers'] = len(self.streamers.get_ids())
        games_from_livestreams = {}
        games_from_videos = {}

        for id in self.streamers.get_ids():
            streamer = self.streamers.get(id)

            livestream_history = streamer.get_livestream_history()
            video_history      = streamer.get_video_history()

            for game in livestream_history:
                stats['num_livestreams'] += len(livestream_history[game]['dates'])
                games_from_livestreams[game] = 1
            for game in video_history:
                stats['num_videos'] += len(video_history[game]['dates'])
                games_from_videos[game] = 1

        stats['games_from_livestreams'] = len(games_from_livestreams)
        stats['games_from_videos'] = len(games_from_videos)
        return stats

    # gets {mean, std_dev, min, max, median, total_in_mb} filesizes for files that comprise the streamers data store
    # -> filesizes are in bytes
    def get_filesizes_for_streamers(self):

        # extract filesizes from zip file
        i = 1
        filesizes_uncompressed = []
        filesizes_compressed = []
        with ZipFile('./data/streamers/streamers.zip') as zip_file:
            for filename in zip_file.namelist():
                fileinfo = zip_file.getinfo(filename)
                filesizes_uncompressed.append(fileinfo.file_size)
                filesizes_compressed.append(fileinfo.compress_size)

        # get most stats
        stats_uncompressed = self.calc_stats_from_list_of_ints(filesizes_uncompressed)
        stats_compressed   = self.calc_stats_from_list_of_ints(filesizes_compressed)

        # get total_in_mb
        total_uncompressed, total_compressed = 0, 0
        for i in range(len(filesizes_uncompressed)):
            total_uncompressed += filesizes_uncompressed[i] / 1000000
            total_compressed   += filesizes_compressed[i] / 1000000

        stats_uncompressed['total_in_mb'] = round(total_uncompressed, 2)
        stats_compressed['total_in_mb']   = round(total_compressed, 2)

        stats = {'compressed': stats_compressed, 'uncompressed': stats_uncompressed}
        return stats


    # compiles stats about a list of ints
    def calc_stats_from_list_of_ints(self, list_of_ints):
        stats = {'n': 0, 'mean': 0, 'min': -1, 'max': -1, 'median': 0, 'std_dev': 0}

        stats['n'] = len(list_of_ints)
        if (stats['n'] == 0):
            return stats

        # get median
        list_of_ints.sort()
        midpoint = int(stats['n'] / 2)
        stats['median'] = list_of_ints[midpoint]

        # get mean values
        for val in list_of_ints:
            stats['mean'] += val
            stats['max'] = val if  (val > stats['max']) else stats['max']
            stats['min'] = val if ((val < stats['min']) or (stats['min'] < 0)) else stats['min']
        stats['mean'] = stats['mean'] / stats['n']

        # get variance -> std_dev
        for val in list_of_ints:
            stats['std_dev'] += (stats['mean'] - val) ** 2
        if (stats['n'] > 1):
            stats['std_dev'] = stats['std_dev'] / (stats['n'] - 1)
        stats['std_dev'] = math.sqrt(stats['std_dev'])

        # round values and return
        stats['mean']    = round(stats['mean'], 2)
        stats['std_dev'] = round(stats['std_dev'], 2)
        return stats


    # Gets data about Streamers.known_missing_videos
    def get_stats_about_streamers_missing_videos(self):
        num_streamers = len(self.streamers.known_missing_videos.streamers)
        stats = {'n': num_streamers}
        return stats

    # Specific Streamer --------------------------------------------------------

    # prints info about a specific streamer
    def print_streamer_by_streamer_id(self, streamer_id):
        print(self.streamers.get(streamer_id))

    def print_streamer_by_io_id(self, io_id):
        streamer_id = self.streamers.io_to_streamer_lookup[io_id]
        print('io_id:', io_id, 'streamer_id:', streamer_id)
        print(self.streamers.get(streamer_id))

# ==============================================================================
# RUN
# ==============================================================================

def print_dict(d):
    for k, v in d.items():
        print(k, "\n ->", v, "\n")

def run():
    insights = Insights('cli')
    results = insights.get_snapshot_of_streamers_db()
    print_dict(results)

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
