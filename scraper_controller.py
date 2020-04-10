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
import threading

from scraper import *


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

def thread_scrape_livestreams(thread_id):
    print('this function is for scraping livestreams')
    while(1):
        if (work[thread_id]['status'] == 'waiting'):
            work[thread_id]['status'] = 'working'
            print('thread: ', thread_id)

            work[thread_id]['status'] = 'done'
            time.sleep(1) # * 60 * 15) # sleep for 15 minutes

# Scrape Videos ----------------------------------------------------------------

def thread_scrape_videos(thread_id):
    print('this function is for scraping videos')
    while(1):
        print('thread: ', thread_id)
        time.sleep(5) # never sleep

# Scrape Followers -------------------------------------------------------------

def thread_scrape_followers(thread_id):
    print('this function is for scraping followers')
    while(1):
        print('thread: ', thread_id)
        time.sleep(2) # sleep for


# ==============================================================================
# Main
# ==============================================================================

def main_thread():

    # instantiate Streamers
    streamers = Streamers()

    # instantiate Threads and start them running
    worker_threads['livestreams'] = threading.Thread(target=thread_scrape_livestreams, args=('livestreams', ))
    worker_threads['videos']      = threading.Thread(target=thread_scrape_videos, args=('videos', ))
    worker_threads['followers']   = threading.Thread(target=thread_scrape_followers, args=('followers', ))
    for thread_id in worker_threads:
        work[thread_id] = {'streamers': streamers.clone(), 'status': 'waiting'} # <- TODO: change to streamers.clone()
        worker_threads[thread_id].start()

    # wait until there is work to be done
    while(1):

        for thread_id in work:
            if (work[thread_id]['status'] == 'done'):
                streamers.merge(work[thread_id]['streamers'])
                work[thread_id]['streamers'] = streamers.clone()
                work[thread_id]['status'] = 'working'
                streamers.export_to_csv()
        time.sleep(1)



# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    print('This program is not functional on this commit.')
    return
    main_thread()
