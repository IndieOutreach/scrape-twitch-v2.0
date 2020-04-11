# ==============================================================================
# About
# ==============================================================================
#
# ScraperController.py is the program you run when you want to compile data about streamers over long periods of time
# - It will run continuously once started (does not have a termination condition)
#   -> Therefore, this is a program you want to run on a production server, not on your laptop
#
# - It will spin off threads to perform certain scraping tasks
#   -> Every 30 minutes, it scrapes all livestreams on Twitch and adds info to streamer profiles
#   -> Once per day, it will scrape follower_count info for every streamer in the database
#   -> Over time, it will scrape video data for every streamer
#

import sys
import time
import json
import datetime
import threading

from scraper import *

# Constants --------------------------------------------------------------------

__no_limit             = 9999999 # <- int that represents positive infinity
__videos_batch_size    = 10      # <- number of streamers to scrape video info for (before saving results and starting again)
__followers_batch_size = 500     # <- number of streamers to scrape follower info for (before saving results and starting again)


__streamers_folderpath              = './data/streamers'
__streamers_missing_videos_filepath = './data/streamers_missing_videos.csv'

# Shared Resources -------------------------------------------------------------

# a shared variable that stores the work/results by each thread.
# Because threads access this object using their thread_id, all active threads can access this variable at the same time
work           = {} # form: { thread_id: { streamers: Streamers(), status: string } }
                    # status can be 1 of the following:
                    # - ready:   the main thread is done with its action and this thread is now ready to work
                    # - working: thread is actively working, main thread leaves this thread alone
                    # - done:    thread is done with its work and is now waiting for the main thread to take its action
worker_threads = {} # form: { thread_id: Thread object }

# ==============================================================================
# ScraperController
# ==============================================================================

# Scrape Livestreams -----------------------------------------------------------

# scrapes all livestreams currently active on Twitch
def thread_scrape_livestreams(thread_id):
    credentials = open('credentials.json')
    scraper = Scraper(json.load(credentials), 'headless')

    while(1):
        if (work[thread_id]['status'] == 'waiting'):
            work[thread_id]['status'] = 'working'
            print(str(datetime.datetime.now().time()), thread_id, ": woken up by main thread. Starting work now.")
            work[thread_id]['streamers'] = scraper.compile_streamers_db(work[thread_id]['streamers'])
            print(str(datetime.datetime.now().time()), thread_id, ": work complete; sleeping for 15 minutes")
            work[thread_id]['status'] = 'done'
            time.sleep(15) # * 60 * 15) # sleep for 15 minutes

# Scrape Videos ----------------------------------------------------------------

# scrapes in batches of 10 streamers at a time so videos don't get lost
def thread_scrape_videos(thread_id):
    credentials = open('credentials.json')
    scraper = Scraper(json.load(credentials), 'headless')

    while(1):
        if (work[thread_id]['status'] == 'waiting'):
            work[thread_id]['status'] = 'working'
            print(str(datetime.datetime.now().time()), thread_id, ": woken up by main thread. Starting work now.")
            work[thread_id]['streamers'] = scraper.add_videos_to_streamers_db(work[thread_id]['streamers'], __no_limit, __videos_batch_size)
            print(str(datetime.datetime.now().time()), thread_id, ": work complete; sleeping until woken up by Main Thread")
            work[thread_id]['status'] = 'done'

# Scrape Followers -------------------------------------------------------------

def thread_scrape_followers(thread_id):
    credentials = open('credentials.json')
    scraper = Scraper(json.load(credentials), 'headless')

    while(1):
        if (work[thread_id]['status'] == 'waiting'):
            work[thread_id]['status'] = 'working'
            print(str(datetime.datetime.now().time()), thread_id, ": woken up by main thread. Starting work now.")
            work[thread_id]['streamers'] = scraper.add_followers_to_streamers_db(work[thread_id]['streamers'], __followers_batch_size)
            print(str(datetime.datetime.now().time()), thread_id, ": work complete; sleeping until woken up by Main Thread")
            work[thread_id]['status'] = 'done'


# ==============================================================================
# Main
# ==============================================================================

def main_thread():

    # instantiate Streamers
    streamers = Streamers(__streamers_folderpath, __streamers_missing_videos_filepath)

    # instantiate Threads and start them running
    worker_threads['livestreams'] = threading.Thread(target=thread_scrape_livestreams, args=('livestreams', ))
    worker_threads['videos']      = threading.Thread(target=thread_scrape_videos, args=('videos', ))
    worker_threads['followers']   = threading.Thread(target=thread_scrape_followers, args=('followers', ))
    for thread_id in worker_threads:
        work[thread_id] = {'streamers': streamers.clone(), 'status': 'waiting'} # <- TODO: change to streamers.clone()
        worker_threads[thread_id].start()


    # wait (spin) until there is work to be done
    # TODO: change this to be a conditional variable
    while(1):
        for thread_id in work:
            if (work[thread_id]['status'] == 'done'):
                streamers.merge(work[thread_id]['streamers'])
                streamers.export_to_csv(__streamers_folderpath)
                work[thread_id]['streamers'] = streamers.clone()
                work[thread_id]['status'] = 'waiting'
                time.sleep(1)

    print('We should not have been able to get here...')

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main_thread()
