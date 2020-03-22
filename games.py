# ==============================================================================
# About
# ==============================================================================
#
# games.py contains the Game and Games classes
# - A Game is an object that contains info about a game
# - Games is a collection of Game objects and is responsible for bulk operations like importing/exporting to/from CSV

# Imports ----------------------------------------------------------------------

import sys
import json

# ==============================================================================
# Game Class
# ==============================================================================

class Game():

    def __init__(self, igdb_game_obj):
        self.id   = self.__get(igdb_game_obj, 'id', False)
        self.name = self.__get(igdb_game_obj, 'name', False)
        self.genres = self.__get(igdb_game_obj, 'genres', False)
        self.keywords = self.__get(igdb_game_obj, 'keywords', False)
        self.themes = self.__get(igdb_game_obj, 'themes', False)
        self.platforms = self.__get(igdb_game_obj, 'platforms', False)
        self.collection = self.__get(igdb_game_obj, 'collection', False)
        self.release_date = self.__get(igdb_game_obj, 'first_release_date', False)
        self.game_modes = self.__get(igdb_game_obj, 'game_modes', False)
        self.player_perspectives = self.__get(igdb_game_obj, 'player_perspectives', False)
        self.popularity = self.__get(igdb_game_obj, 'popularity', False)
        self.similar_games = self.__get(igdb_game_obj, 'similar_games', False)
        self.time_to_beat = self.__get(igdb_game_obj, 'time_to_beat', False)
        self.age_ratings = self.__get(igdb_game_obj, 'age_ratings', False)
        self.category = self.__get(igdb_game_obj, 'category', False)
        self.igdb_box_art_url = -1


    # safely extracts info from a dictionary
    def __get(obj, key, default):
        if (key in obj):
            return obj[key]
        return default

# ==============================================================================
# Games Class
# ==============================================================================

class Games():

    def __init__(self):
        self.games = {}

    # declares a new Game object and adds it to the collection of games
    def add_new_game(self, igdb_game_obj):
        game_id = igdb_game_obj['id']
        if (game_id not in self.games):
            self.games[game_id] = Game(igdb_game_obj)


    def print_stats(self):
        print("number of items in collection: ", len(self.games))
