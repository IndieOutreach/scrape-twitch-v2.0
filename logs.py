# ==============================================================================
# About
# ==============================================================================
#
# logs.py contains different classes for logging things
# - TimeLogs: logs the time taken for API requests
# - FilterLogs: logs the number of livestreams that are filtered out during the Scraper.compile_streamers_db() step
#

# Imports ----------------------------------------------------------------------

import sys
import csv
import time
import math

# ==============================================================================
# TimeLogs
# ==============================================================================

# class is used to record timing and number of different actions (ie: API requests)
# - It is imported by TwitchAPI
# NOTE: all times are in milliseconds
class TimeLogs():

    def __init__(self, action_categories):
        self.logs = {} # { request_name: [ {request_obj}, ... ] }
        for type in action_categories:
            self.logs[type] = []
        self.time_initialized = self.__get_current_time()


    # Actions ------------------------------------------------------------------

    def start_action(self, action_type):

        # case 0: this action type DNE and needs to be registered
        if (action_type not in self.logs):
            self.logs[action_type] = [ {'start': self.__get_current_time(), 'end': 0} ]
            return

        # case 1: there are no actions on record
        if (len(self.logs[action_type]) == 0):
            self.logs[action_type].append({'start': self.__get_current_time(), 'end': 0})
            return

        # case 2: the latest action is already finished so we can register a new one
        # -> note: if the current action is not finished yet, we can't do anything
        current_action = self.logs[action_type][-1]
        if (current_action['end'] > 0):
            self.logs[action_type].append({'start': self.__get_current_time(), 'end': 0})
            return


    def end_action(self, action_type):

        if ((action_type not in self.logs) or (len(self.logs[action_type]) == 0)):
            return

        last_index = len(self.logs[action_type]) - 1
        if (self.logs[action_type][last_index]['end'] == 0):
            self.logs[action_type][last_index]['end'] = self.__get_current_time()


    def get_time_since_start(self):
        t = self.__get_current_time() - self.time_initialized
        return round(t, 2)


    # returns the current time in milliseconds
    def __get_current_time(self):
        return int(round(time.time() * 1000))

    # Stats --------------------------------------------------------------------

    def print_stats(self):
        for action_category, actions in self.logs.items():
            stats = self.__calc_stats_about_action(actions)
            print("Request: ", action_category)
            print(" - total: ", stats['n'], "requests")
            if (len(actions) > 0):
                print(" - mean: ", stats['mean'], "ms")
                print(" - std_dev: ", stats['std_dev'], "ms")
                print(" - min: ", stats['min'], "ms")
                print(" - max: ", stats['max'], "ms")
        print("Total Time: ", self.get_time_since_start(), "ms")

    # gets stats about each request in logs
    def get_stats_from_logs(self):
        stats = {}
        for action_category, actions in self.logs.items():
            if (len(actions) > 0):
                stats[action_category] = self.__calc_stats_about_action(actions)
        return stats

    def __calc_stats_about_action(self, actions):

        first_start, last_end = False, False
        min_val, max_val   = 9999999, -1
        mean, var, std_dev = 0, 0, 0

        if (len(actions) == 0):
            return {'n': 0, 'min': 0, 'max': 0, 'std_dev': 0, 'first_start': 0, 'last_end': 0}

        # convert actions from {'start', 'end'} objects into time_per_action
        times = []
        for action in actions:
            if (action['end'] > 0):
                time_took = action['end'] - action['start']
                times.append(time_took)
                min_val = time_took if (time_took < min_val) else min_val
                max_val = time_took if (time_took > max_val) else max_val

                first_start = action['start'] if ((first_start == False) or (action['start'] < first_start)) else first_start
                last_end = action['end'] if ((last_end == False) or (action['end'] > last_end)) else last_end

        # calc mean
        for t in times:
            mean += t
        mean = mean / len(times)

        # calc std_dev
        for t in times:
            var += (mean - t) ** 2
        if (len(times) > 1):
            var = var / (len(times) - 1)
        std_dev = math.sqrt(var)

        stats = {
            'n': len(actions),
            'min': min_val,
            'max': max_val,
            'mean': round(mean, 2),
            'std_dev': round(std_dev, 2),
            'first_start': first_start,
            'last_end': last_end
        }
        return stats


    # File I/O -----------------------------------------------------------------

    # NOTE: TimeLogs is an individual log entry.
    # -> In order to save and not overwrite previous logs, need to load them as an array and add current TimeLog to the end
    def export_to_csv(self, filename, content_type, num_items):
        # get content ready
        content = self.load_from_csv(filename)
        content.append({
            'time_started': self.time_initialized,
            'time_ended': self.__get_current_time(),
            'content_type': content_type,
            'logs': self.get_stats_from_logs(),
            'num_items': num_items
        })

        # write file
        fieldnames = ['time_started', 'time_ended', 'content_type', 'num_items', 'logs']
        filename = filename if ('.csv' in filename) else filename + '.csv'
        with open(filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in content:
                writer.writerow(row)


    def load_from_csv(self, filename):
        contents = []
        filename = filename if ('.csv' in filename) else filename + '.csv'
        try:
            with open(filename) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    contents.append(row)
        except IOError:
            print(filename, "does not exist yet")

        return contents


# ==============================================================================
# FilterLogs
# ==============================================================================

# a relatively simple class for loading from / exporting to the '/logs/filters.csv' file
class FilterLogs():

    def __init__(self, filename = False):
        if (filename != False):
            self.filename = filename if ('.csv' in filename) else filename + '.csv'
            self.content = self.load_from_csv(self.filename)
        else:
            self.filename = False
            self.content = []
        return

    def add_filter(self, num_scraped, num_filtered, view_cutoff, breakdown_obj):
        self.content.append({
            'time': int(time.time()),
            'scraped': num_scraped,
            'filtered': num_filtered,
            'view_cutoff': view_cutoff,
            'breakdown': breakdown_obj
        })

    def export_to_csv(self, filename = False):

        if (filename == False and self.filename == False):
            return

        fieldnames = ['time', 'scraped', 'filtered', 'view_cutoff', 'breakdown']
        filename = filename if (filename != False) else self.filename
        filename = filename if ('.csv' in filename) else filename + '.csv'
        with open(self.filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.content:
                writer.writerow(row)


    def load_from_csv(self, filename = False):
        contents = []
        filename = filename if (filename != False) else self.filename
        filename = filename if ('.csv' in filename) else filename + '.csv'
        try:
            with open(filename) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    contents.append(row)
        except IOError:
            print(filename, "does not exist yet")

        return contents

# ==============================================================================
# GeneralLogs
# ==============================================================================

class GeneralLogs():

    def __init__(self, filename = False):
        if (filename != False):
            self.filename = filename
            self.content = self.load_from_csv(self.filename)
        else:
            self.filename = False
            self.content = False
        return

    # adds an item to contents
    def add(self, item):
        item['time'] = int(time.time())
        self.content.append(item)

    # returns all fieldnames that appear in content
    def get_fieldnames(self):
        fieldnames = ['time']
        for row in self.content:
            for key in row:
                if (key not in fieldnames):
                    fieldnames.append(key)
        fieldnames.sort()
        return fieldnames

    # returns
    def get_contents_with_all_fields(self, fieldnames = False):
        fieldnames = self.get_fieldnames() if (fieldnames == False) else fieldnames
        contents = []
        for row in self.content:
            item = {}
            for key in fieldnames:
                if (key in row):
                    item[key] = row[key]
                else:
                    item[key] = '' # <- Null value
            contents.append(item)
        return contents


    def export_to_csv(self, filename = False):

        if (filename == False and self.filename == False):
            return

        fieldnames = self.get_fieldnames()
        filename = filename if (filename != False) else self.filename
        filename = filename if ('.csv' in filename) else filename + '.csv'
        with open(self.filename, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.get_contents_with_all_fields(fieldnames):
                writer.writerow(row)


    def load_from_csv(self, filename = False):
        contents = []
        filename = filename if (filename != False) else self.filename
        filename = filename if ('.csv' in filename) else filename + '.csv'
        try:
            with open(filename) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    contents.append(row)
        except IOError:
            print(filename, "does not exist yet")

        return contents
