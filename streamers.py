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

    def __init__(self, twitch_obj, is_livestream = True):

        # livestreams and videos have different access keys
        date_key = 'started_at' if (is_livestream) else 'created_at'
        views_key = 'viewer_count' if (is_livestream) else 'view_count'

        # convert Twitch's UTC Format to Unix Epoch
        day = twitch_obj[date_key].split("T")[0] # <- we only care about data on the day/month/year level
        epoch = int(datetime.datetime.strptime(day, '%Y-%m-%d').timestamp())

        self.id             = int(twitch_obj['id'])
        self.user_id        = twitch_obj['user_id']
        self.twitch_game_id = twitch_obj['game_id'] if ('game_id' in twitch_obj) else 0
        self.game_name      = twitch_obj['game_name'] if ('game_name' in twitch_obj) else ""
        self.language       = twitch_obj['language']
        self.date           = epoch
        self.views          = twitch_obj[views_key]
        self.is_livestream  = is_livestream
        self.title          = twitch_obj['title']


    def print_info(self):
        print("title:", self.title)
        print("id:", self.id, "user:", self.user_id)
        print('game: ', self.twitch_game_id, " - ", self.game_name)
        print("date: ", self.date)
        print("views:", self.views)
        print("livestream: ", self.is_livestream)
        print("-")

# ==============================================================================
# Streamer
# ==============================================================================

class Streamer():

    def __init__(self, streamer_obj, from_csv = False):
        if (from_csv):
            self.id = ""

        else:
            self.id                = int(streamer_obj['id'])
            self.display_name      = streamer_obj['display_name']
            self.profile_image_url = streamer_obj['profile_image_url']
            self.total_views       = streamer_obj['view_count']
            self.description       = streamer_obj['description']
            self.num_followers     = streamer_obj['num_followers'] if ('num_followers' in streamer_obj) else 0
            self.language          = streamer_obj['language'] if ('language' in streamer_obj) else ""
            self.stream_history    = {} # will have format {twitch_game_id: num_times_played}
            self.last_updated      = streamer_obj['last_updated'] if ('last_updated' in streamer_obj) else 0


    # updates profile information w/ new info from Twitch
    def update(self, twitch_obj):
        self.display_name      = streamer_obj['display_name']
        self.profile_image_url = streamer_obj['profile_image_url']
        self.total_views       = streamer_obj['view_count']
        self.description       = streamer_obj['description']
        self.num_followers     = streamer_obj['num_followers'] if ('num_followers' in streamer_obj) else self.num_followers
        self.language          = streamer_obj['language'] if ('language' in streamer_obj) else self.language
        self.last_updated      = streamer_obj['last_updated'] if ('last_updated' in streamer_obj) else self.last_updated


    # adds data from a video or livestream
    def add_stream_data(self, stream):

        # if this stream has already been accounted for, stop
        # if this stream is more recent than our last streamer update, note it
        if ((stream.date == self.last_updated) and (stream.is_livestream)):
            return
        elif ((stream.date > self.last_updated) and (stream.is_livestream)):
            self.last_updated = stream.date

        # add game info
        game_key = stream.twitch_game_id if (stream.is_livestream) else stream.game_name
        views_contributed = stream.views if (stream.is_livestream) else 0
        videos_contributed = 0 if (stream.is_livestream) else 1


        if (game_key in self.stream_history):
            self.stream_history[game_key]['times_played'] += 1
            self.stream_history[game_key]['num_videos'] += videos_contributed
            self.stream_history[game_key]['num_views'] += views_contributed
            self.stream_history[game_key]['dates'].append(stream.date)

        else:
            self.stream_history[game_key] = {
                'times_played': 1,
                'num_views': views_contributed,
                'num_videos': videos_contributed,
                'dates': [stream.date]
            }


    def to_dict(self):
        obj = {
            'id': self.id,
            'display_name': self.display_name,
            'profile_image_url': self.profile_image_url,
            'total_views': self.total_views,
            'description': self.description,
            'num_followers': self.num_followers,
            'language': self.language,
            'stream_history': self.stream_history,
            'last_updated': self.last_updated
        }
        return obj


# ==============================================================================
# Streamers
# ==============================================================================


class Streamers():

    def __init__(self, filepath = False):
        self.streamers = {}

    # get ----------------------------------------------------------------------

    # returns a specified streamer
    def get(self, streamer_id):
        if (streamer_id in self.streamers):
            return self.streamers[streamer_id]
        return False

    # returns a list of all streamer IDs in collection
    def get_streamer_ids(self):
        return list(self.streamers.keys())

    # insert -------------------------------------------------------------------

    # inserts a new streamer into the collection
    def add_or_update_streamer(self, twitch_obj):
        streamer_id = twitch_obj['user_id'] if ('user_id' in twitch_obj) else twitch_obj['id']
        if (streamer_id not in self.streamers):
            self.streamers[streamer_id] = Streamer(twitch_obj)
        else:
            self.streamers[streamer_id].update(twitch_obj)

    # for a specific streamer, add video/livestream data
    def add_stream_data(self, stream):
        if (stream.user_id in self.streamers):
            self.streamers[stream.user_id].add_stream_data(stream)
