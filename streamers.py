# ==============================================================================
# About
# ==============================================================================
#
# streamers.py contains the Stream, Streamer, and Streamers classes
# - Stream is the representation of a livestream or video
# - Streamer is a Twitch streamer
# - Streamers is a collection of streamers and is responsible for all bulk operations like importing/exporting from csv
#

# Imports ----------------------------------------------------------------------

import sys
import csv
import json
import datetime

# ==============================================================================
# Stream
# ==============================================================================

class Stream():

    def __init__(self, twitch_obj):

        # convert Twitch's UTC Format to Unix Epoch
        day = twitch_obj['started_at'].split("T")[0] # <- we only care about data on the day/month/year level
        epoch = int(datetime.datetime.strptime(day, '%Y-%m-%d').timestamp())

        self.id             = twitch_obj['id']
        self.user_id        = twitch_obj['user_id']
        self.twitch_game_id = twitch_obj['game_id']
        self.language       = twitch_obj['language']
        self.date           = epoch
        self.views          = twitch_obj['viewer_count']


# ==============================================================================
# Streamer
# ==============================================================================

class Streamer():

    def __init__(self, streamer_obj, from_csv = False):
        if (from_csv):
            self.id = ""

        else:
            self.id = ""


# ==============================================================================
# Streamers
# ==============================================================================


class Streamers():

    def __init__(self, filepath = False):
        self.streamers = {}


    def get(self, streamer_id):
        if (streamer_id in self.streamers):
            return self.streamers[streamer_id]
        return False

    def add_new_streamer(self, twitch_obj):
        streamer_id = twitch_obj['user_id']
        if (streamer_id not in self.streamers):
            self.streamers[streamer_id] = Streamer(twitch_obj)
