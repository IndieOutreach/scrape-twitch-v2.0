# ==============================================================================
# About
# ==============================================================================
#
# insights.py is a script for drawing insights from our data:
# - games.csv
# - streamers.csv
#

import sys

from games import *
from streamers import *

# ==============================================================================
# Class: Insights
# ==============================================================================

class Insights():

    def __init__(self):
        self.set_dataset('production')
        return

    # loads datasets
    def set_dataset(self, mode):
        if (mode == 'production'):
            self.streamers = Streamers('./data/streamers.csv')
            self.games = Games('./data/games.csv')
        elif (mode == 'testing'):
            self.streamers = Streamers('./test/streamers.csv')
            self.games = Games('./data/games.csv')


    # Streamers ----------------------------------------------------------------

    # Questions this function answers:
    # - how many streamers are there?
    # - how many streamers have video data? How many don't?
    # - Follower Data
    #   -> what is the max counts of follower data a streamer has? How many have that number? That number - 1? etc
    #   -> how many streamers have follower data from the past day? past week? past month?
    # - Views Data
    #   -> what is the typical number of view_count objects for a streamer?
    # - Stream History
    #   -> how many games have been played?
    #   -> what percentage of streamers have videos?
    #   -> how many livestreams is typical for each streamer?
    def get_general_streamer_stats(self):

        print('.get_general_streamer_stats() is under construction. Please check back later')
        return

        for id in self.streamers.get_ids():
            print(id)


    # Streamer: Irregularity Detection -----------------------------------------

    # This function is useful for spotting possible errors or irregularities in the data
    # Questions this function answers
    # - How many streamers don't have videos?
    # - How many streamers don't have livestreams from the last day?
    # - How many streamers don't have a view count from the last day?
    # - How many streamers don't have a follower count from the last day?
    def get_streamer_irregularities(self):

        results = {
            'num_streamers': 0,
            'missing_videos': {'percentage': 0, 'number': 0},
            'followers_past_day': {'percentage': 0, 'number': 0},
            'livestreamed_past_day': {'percentage': 0, 'number': 0},
            'livestreamed_past_week': {'percentage': 0, 'number': 0},
            'has_view_data_past_day': {'percentage': 0, 'number': 0}
        }

        # variables
        num_streamers = len(self.streamers.get_ids())
        time_today = int(time.time())
        time_yesterday = time_today - (60*60*24) # <- seconds*minutes*hours
        time_week = time_today - (60*60*24*7)


        # Q: How many streamers don't have videos?
        num_no_video_ids = len(self.streamers.get_ids_with_no_video_data())
        results['num_streamers'] = num_streamers
        results['missing_videos']['percentage'] = round(num_no_video_ids / num_streamers * 100, 2)
        results['missing_videos']['number'] = num_no_video_ids

        # Q: How many streamers don't have follower data from last day?
        num_no_followers = len(self.streamers.get_ids_with_missing_follower_data())
        results['followers_past_day']['number'] = num_streamers - num_no_followers
        results['followers_past_day']['percentage'] = round(100 - (num_no_followers / num_streamers * 100), 2)

        # Q: How many streamers livestreamed during the past day? past week?
        num_past_day = len(self.streamers.get_ids_who_livestreamed_in_range(time_yesterday, time_today))
        num_past_week = len(self.streamers.get_ids_who_livestreamed_in_range(time_week, time_today))
        results['livestreamed_past_day']['number'] = num_past_day
        results['livestreamed_past_day']['percentage'] = round(num_past_day / num_streamers * 100, 2)
        results['livestreamed_past_week']['number'] = num_past_week
        results['livestreamed_past_week']['percentage'] = round(num_past_week / num_streamers * 100, 2)

        # Q: How many streamers have view counts from the last day?
        num_view_counts = len(self.streamers.get_ids_with_view_counts_in_range(time_yesterday, time_today))
        results['has_view_data_past_day']['percentage'] = round(num_view_counts / num_streamers * 100, 2)
        results['has_view_data_past_day']['number'] = num_view_counts

        return results

# ==============================================================================
# RUN
# ==============================================================================

def print_dict(d):
    for k, v in d.items():
        print(k)
        print(" ->", v)
        print('.')

def run():
    insights = Insights()
    results = insights.get_streamer_irregularities()
    print_dict(results)

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    run()
