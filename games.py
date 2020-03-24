# ==============================================================================
# About
# ==============================================================================
#
# games.py contains the Game and Games classes
# - A Game is an object that contains info about a game
# - Games is a collection of Game objects and is responsible for bulk operations like importing/exporting to/from CSV

# Imports ----------------------------------------------------------------------

import sys
import csv
import json

# ==============================================================================
# Game Class
# ==============================================================================

class Game():

    # if from_csv is True, we are loading this game from a row in a CSV file
    # otherwise, if CSV is False, then we are loading from an IGDB search result
    def __init__(self, game_obj, from_csv = False):

        if (from_csv):

            # loaded from CSV -> need to re-type all the variables
            self.id                  = int(self.__get(game_obj, 'id', 0))
            self.name                = self.__get(game_obj, 'name', "")
            self.genres              = json.loads(self.__get(game_obj, 'genres', []))
            self.keywords            = json.loads(self.__get(game_obj, 'keywords', []))
            self.themes              = json.loads(self.__get(game_obj, 'themes', []))
            self.platforms           = json.loads(self.__get(game_obj, 'platforms', []))
            self.collection          = int(self.__get(game_obj, 'collection', 0))
            self.release_date        = int(self.__get(game_obj, 'release_date', 0))
            self.game_modes          = json.loads(self.__get(game_obj, 'game_modes', []))
            self.player_perspectives = json.loads(self.__get(game_obj, 'player_perspectives', []))
            self.popularity          = float(self.__get(game_obj, 'popularity', 0))
            self.similar_games       = json.loads(self.__get(game_obj, 'similar_games', []))
            self.time_to_beat        = int(self.__get(game_obj, 'time_to_beat', 0))
            self.age_ratings         = json.loads(self.__get(game_obj, 'age_ratings', []))
            self.category            = int(self.__get(game_obj, 'category', 0))
            self.igdb_box_art_url    = self.__get(game_obj, 'igdb_box_art_url', "")
            self.twitch_box_art_url  = self.__get(game_obj, 'twitch_box_art_url', "")
            self.release_date        = int(self.__get(game_obj, 'release_date', 0))
            self.twitch_box_art_url  = ""
        else:

            # loaded from the igdb API -> types are all in place
            self.id                  = self.__get(game_obj, 'id', 0)
            self.name                = self.__get(game_obj, 'name', "")
            self.genres              = self.__get(game_obj, 'genres', [])
            self.keywords            = self.__get(game_obj, 'keywords', [])
            self.themes              = self.__get(game_obj, 'themes', [])
            self.platforms           = self.__get(game_obj, 'platforms', [])
            self.collection          = self.__get(game_obj, 'collection', 0)
            self.release_date        = self.__get(game_obj, 'release_date', 0)
            self.game_modes          = self.__get(game_obj, 'game_modes', [])
            self.player_perspectives = self.__get(game_obj, 'player_perspectives', [])
            self.popularity          = self.__get(game_obj, 'popularity', 0)
            self.similar_games       = self.__get(game_obj, 'similar_games', [])
            self.time_to_beat        = self.__get(game_obj, 'time_to_beat', 0)
            self.age_ratings         = self.__get(game_obj, 'age_ratings', [])
            self.category            = self.__get(game_obj, 'category', 0)
            self.igdb_box_art_url    = self.__get(game_obj, 'igdb_box_art_url', "")
            self.twitch_box_art_url  = self.__get(game_obj, 'twitch_box_art_url', "")
            self.release_date        = self.__get(game_obj, 'first_release_date', 0)
            self.twitch_box_art_url  = "" # <- this value isn't part of the igdb game obj, so will be updated int he future


    # safely extracts info from a dictionary
    def __get(self, obj, key, default):
        if (key in obj):
            return obj[key]
        return default

    def to_dict(self):
        obj = {
            'id': self.id,
            'name': self.name,
            'genres': self.genres,
            'keywords': self.keywords,
            'themes': self.themes,
            'platforms': self.platforms,
            'collection': self.collection,
            'release_date': self.release_date,
            'game_modes': self.game_modes,
            'player_perspectives': self.player_perspectives,
            'popularity': self.popularity,
            'similar_games': self.similar_games,
            'time_to_beat': self.time_to_beat,
            'age_ratings': self.age_ratings,
            'category': self.category,
            'igdb_box_art_url': self.igdb_box_art_url,
            'twitch_box_art_url': self.twitch_box_art_url
        }
        return obj

# ==============================================================================
# Games Class
# ==============================================================================

class Games():

    def __init__(self, filename = False):
        self.games = {}
        if (filename):
            self.load_from_csv(filename)

    # declares a new Game object and adds it to the collection of games
    def add_new_game(self, igdb_game_obj):
        game_id = igdb_game_obj['id']
        if (game_id not in self.games):
            self.games[game_id] = Game(igdb_game_obj)


    # Get ----------------------------------------------------------------------

    def get(self, game_id):
        if (game_id in self.games):
            return self.games[game_id]
        return False

    def get_ids(self):
        return self.games.keys()

    def print_stats(self):
        print("number of Games in collection: ", len(self.games))

    # File I/O -----------------------------------------------------------------

    def export_to_csv(self, filename):
        fieldnames = [
            'id', 'name', 'genres', 'keywords', 'themes', 'platforms', 'collection', 'release_date',
            'game_modes', 'player_perspectives', 'popularity', 'similar_games', 'time_to_beat',
            'age_ratings', 'category', 'igdb_box_art_url', 'twitch_box_art_url'
        ]

        filename = filename if ('.csv' in filename) else filename + '.csv'
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for game_id, game in self.games.items():
                writer.writerow(game.to_dict())


    def load_from_csv(self, filename):
        filename = filename if ('.csv' in filename) else filename + '.csv'
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                game = Game(row, True)
                self.games[game.id] = game


    # Data Validation ----------------------------------------------------------

    # compares this Games object with another Games object
    # returns true if they point at the exact same games
    def check_if_game_collections_same(self, games2):

        # case 0: there are an uneven number of games in each collection
        if (len(self.games) != len(games2.games)):
            return False

        for game_id in self.games:

            game1 = self.get(game_id)
            game2 = games2.get(game_id)

            # case 1: 1 collection has a specified game when the other does not
            if ((game1 == False) or (game2 == False)):
                return False

            obj1 = game1.to_dict()
            obj2 = game2.to_dict()

            # case 2: the collection's Game objects have a different number of parameters
            if (len(obj1) != len(obj2)):
                return False

            for key in obj1:
                val1 = obj1[key]
                if (key not in obj2): # case 3: one Game has a parameter that the other lacks
                    return False
                val2 = obj2[key]

                if (val1 != val2): # case 4: the values of parameters are different between the two Games
                    return False

        return True
