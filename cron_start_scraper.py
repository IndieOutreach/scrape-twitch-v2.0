# ==============================================================================
# About
# ==============================================================================
#
# cron_start_scraper.py checks the scraper's logs to see if it has been running recently
# -> if it hasn't, it runs scraper_controller.py
#
# To setup the cron job, initialize this script to run every 30 minutes
# - cron: '*/30 * * * * python cron_start_scraper.py'
#
# For help with cron, follow instructions at 
# - https://www.ostechnix.com/a-beginners-guide-to-cron-jobs/
#

import sys
import csv
import time
import datetime

from logs import *
import scraper_controller


__refresh_limit = 60 * 45  # <- 45 minutes

# Log File ---------------------------------------------------------------------

# load from csv
def load_from_csv(filename = './data/requests.csv'):
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


# Main -------------------------------------------------------------------------

def main():
    current_month = datetime.datetime.now().strftime("%Y-%m")
    filepath = './logs/requests[' + current_month + '].csv'
    logs = load_from_csv(filepath)

    current_time = int(time.time())
    time_of_last_request = 0 if (len(logs) == 0) else int(logs[-1]['time_ended']) / 1000
    time_since_last_request = current_time - time_of_last_request

    if (time_since_last_request > __refresh_limit):
        scraper_controller.main_thread()
    else:
        print('The last scraper request was made too recently to re-run the scraper from this script')
        print(' - time since last request = ', round(time_since_last_request, 2), 'seconds')
        print(' - will be ready to run again in: ', round(__refresh_limit - time_since_last_request, 2), 'seconds')


# Run --------------------------------------------------------------------------
if (__name__ == '__main__'):
    main()
