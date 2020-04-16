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
from insights import *

# Constants --------------------------------------------------------------------

# unique IDs that each thread uses to access its dedicated resources
__thread_id_main        = 'main'
__thread_id_livestreams = 'livestreams'
__thread_id_videos      = 'videos'
__thread_id_followers   = 'followers'


# limit values to pass into Scraper API calls
__no_limit             = 9999999 # <- int that represents positive infinity
__videos_batch_size    = 10      # <- number of streamers to scrape video info for (before saving results and starting again)
__followers_batch_size = 500     # <- number of streamers to scrape follower info for (before saving results and starting again)


# filepaths to load Streamers from
__streamers_folderpath              = './data/streamers'
__streamers_missing_videos_filepath = './data/streamers_missing_videos.csv'

# Time each thread will sleep for after executing
__sleep_between_livestreams   = 60 * 15 # <- 15 minutes
__sleep_when_out_of_videos    = 60 * 3  # <- 3 minutes
__sleep_when_out_of_followers = 60 * 3  # <- 3 minutes
if (False):
    __sleep_between_livestreams   = 10 # <- values used during testing
    __sleep_when_out_of_videos    = 10
    __sleep_when_out_of_followers = 10

# Syncing threads
__thread_timeout = 60 * 60 * 1.5  # <- time it takes for a thread to be considered 'lost' by main thread
                                  # We arbitrarily pick 1.5 hours as our limit.
                                  # No thread operation should take this long. If it does, something has gone wrong

# Shared Resources -------------------------------------------------------------

# a shared variable that stores the work/results by each thread.
# Because threads access this object using their thread_id, all active threads can access this variable at the same time
work = {}   # form: { thread_id: { streamers: Streamers(), status: string, last_started_work: int_date, request_logs: TimeLogs() } }
            # status can be 1 of the following:
            #   - waiting:      the main thread is done with its action and this thread is now ready to work
            #   - working:      thread is actively working, main thread leaves this thread alone
            #   - done:         thread is done with its work and is now waiting for the main thread to take its action
            #   - needs_update: thread *needs* its Streamers() object updated in order to run properly
            #                  - For example: the Videos thread has a Streamers() object with .get_ids_that_need_video_data() == 0
            #                               -> this thread will be useless until the Main Thread updates Streamer
            # streamers is a Streamers() object that the thread is working on / updating
            # last_started_work is a unix epoch date indicating when the thread was last called to start working
            #   - If last_started_work is too long ago, we presume that thre thread is lost and the main thread will kill and restart it
            # request_logs is an instance of TimeLogs() that that thread's scraper is using
            #   - this instance is merged into the TimeLogs instance on the main thread to be exported
            #   - request_logs is wiped/renewed every time the thread starts working

worker_threads = {} # form: { thread_id: Thread object }
thread_locks   = {} # form: { thread_id: Conditional Variable }
                    # -> This CV works as a way for the Main Thread to wake up a worker thread

# ==============================================================================
# ScraperController
# ==============================================================================

# Scrape Livestreams -----------------------------------------------------------

# scrapes all livestreams currently active on Twitch
def thread_scrape_livestreams(thread_id):
    credentials = open('credentials.json')
    scraper = Scraper(json.load(credentials), 'production')

    print_from_thread(thread_id, 'initialized')

    while(1):

        # wait for thread to be woken up by main thread
        wait_for_work_from_main(thread_id)

        # wait_for_work_from_main() can also let a thread that has expired through, so check if we need to kill it
        if (check_if_thread_expired(thread_id)):
            thread_locks[thread_id].release()
            break

        # do the work for the thread
        scraper.twitchAPI.request_logs.reset()
        work[thread_id]['status'] = 'working'
        work[thread_id]['last_started_work'] = get_current_time()
        print_from_thread(thread_id, 'woken up by main thread; starting work now')
        work[thread_id]['streamers'] = scraper.compile_streamers_db(work[thread_id]['streamers'])

        # done
        print_from_thread(thread_id, 'work complete; sleeping until woken up by main thread')
        work[thread_id]['request_logs'] = scraper.twitchAPI.request_logs.clone()
        work[thread_id]['status'] = 'done'
        thread_locks[thread_id].release()
        wake_main_thread()
        time.sleep(__sleep_between_livestreams)

    print_from_thread(thread_id, 'terminating')


# Scrape Videos ----------------------------------------------------------------

# scrapes in batches of 10 streamers at a time so videos don't get lost
def thread_scrape_videos(thread_id):
    credentials = open('credentials.json')
    scraper = Scraper(json.load(credentials), 'production')

    print_from_thread(thread_id, 'initialized')

    while(1):

        # wait for thread to be woken up by main thread
        wait_for_work_from_main(thread_id)

        # wait_for_work_from_main() can also let a thread that has expired through, so check if we need to kill it
        if (check_if_thread_expired(thread_id)):
            thread_locks[thread_id].release()
            break

        # do the work for the thread
        work[thread_id]['status'] = 'working'
        work[thread_id]['last_started_work'] = get_current_time()
        scraper.twitchAPI.request_logs.reset()
        if (len(work[thread_id]['streamers'].get_ids_that_need_video_data()) > 0):
            print_from_thread(thread_id, 'woken up by main thread; starting work now')
            work[thread_id]['streamers'] = scraper.add_videos_to_streamers_db(work[thread_id]['streamers'], __no_limit, __videos_batch_size)
            print_from_thread(thread_id, 'work complete; sleeping until woken up by main thread')
            work[thread_id]['request_logs'] = scraper.twitchAPI.request_logs.clone()
            work[thread_id]['status'] = 'done'
        else:
            work[thread_id]['status'] = 'needs_update'
            time.sleep(__sleep_when_out_of_videos)

        # work is done
        thread_locks[thread_id].release()
        wake_main_thread()

    print_from_thread(thread_id, 'terminating')


# Scrape Followers -------------------------------------------------------------

def thread_scrape_followers(thread_id):
    credentials = open('credentials.json')
    scraper = Scraper(json.load(credentials), 'production')
    print_from_thread(thread_id, 'initialized')

    while(1):

        # wait for thread to be woken up by main thread
        wait_for_work_from_main(thread_id)

        # wait_for_work_from_main() can also let a thread that has expired through, so check if we need to kill it
        if (check_if_thread_expired(thread_id)):
            thread_locks[thread_id].release()
            break

        # do the work for the thread
        work[thread_id]['status'] = 'working'
        work[thread_id]['last_started_work'] = get_current_time()
        scraper.twitchAPI.request_logs.reset()
        if (len(work[thread_id]['streamers'].get_ids_with_missing_follower_data()) > 0):
            print_from_thread(thread_id, "woken up by main thread; starting work now")
            work[thread_id]['streamers'] = scraper.add_followers_to_streamers_db(work[thread_id]['streamers'], __followers_batch_size)
            print_from_thread(thread_id, "work complete; sleeping until woken by main thread")
            work[thread_id]['request_logs'] = scraper.twitchAPI.request_logs.clone()
            work[thread_id]['status'] = 'done'
        else:
            work[thread_id]['status'] = 'needs_update'
            time.sleep(__sleep_when_out_of_followers)


        # work is done -> notify the main thread
        thread_locks[thread_id].release()
        wake_main_thread()

    print_from_thread(thread_id, "terminating...")


# ==============================================================================
# Main
# ==============================================================================

# function that a thread calls when it wants to wait for a lock
def wait_for_work_from_main(thread_id):
    thread_locks[thread_id].acquire()
    while ((not work[thread_id]['status'] == 'waiting') and (not check_if_thread_expired(thread_id))):
        thread_locks[thread_id].wait()
    return

# notifies the main thread that there is work to do
def wake_main_thread():
    thread_locks[__thread_id_main].acquire()
    thread_locks[__thread_id_main].notify_all()
    thread_locks[__thread_id_main].release()


# returns True if there is work to do for Main thread
def check_if_main_should_awake():
    for thread_id in work:
        if (work[thread_id]['status'] == 'done'):
            return True
    for thread_id in worker_threads:
        if (not worker_threads[thread_id].is_alive()):
            return True
    return False


# returns True if a thread has been unproductive for too long and should be terminated
def check_if_thread_expired(thread_id):
    return (get_current_time() - work[thread_id]['last_started_work'] >= __thread_timeout)


# returns the current unix epoch time as an int
def get_current_time():
    return int(time.time())


# prints a message from thread with standard formatting
def print_from_thread(thread_id, message):
    print('{} [ {:11} ] : {}'.format(datetime.datetime.now().time(), thread_id, message))


# creates and runs a worker thread
def create_worker_thread(streamers, thread_id):

    # determine what function thread should run
    starting_function = False
    if (thread_id == __thread_id_livestreams):
        starting_function = thread_scrape_livestreams
    elif (thread_id == __thread_id_videos):
        starting_function = thread_scrape_videos
    elif (thread_id == __thread_id_followers):
        starting_function = thread_scrape_followers
    else:
        return # <- no other threads should exist


    # start the thread
    worker_threads[thread_id] = threading.Thread(target=starting_function, args=(thread_id, ))
    thread_locks[thread_id]   = threading.Condition()
    work[thread_id] = {
        'streamers': streamers.clone(),
        'status': 'waiting',
        'last_started_work': get_current_time(),
        'request_logs': False
    }
    worker_threads[thread_id].daemon = True
    worker_threads[thread_id].start()

# request logs have a dynamically allocated filepath depending on the year/month
# since scraper_controller is meant to run over long periods of time, the controller needs to call this function to refresh the name
def get_request_logs_filepath():
    return datetime.datetime.now().strftime("./logs/requests[%Y-%m].csv")

# Main Thread ------------------------------------------------------------------

# Main thread is in charge of dispatching worker threads and saving results to server
def main_thread():

    # instantiate Streamers
    streamers = Streamers(__streamers_folderpath, __streamers_missing_videos_filepath)
    current_month = datetime.datetime.now().strftime("%Y-%m")
    insights  = Insights('production', current_month)
    insights.set_logging(True)

    # initialize Conditional Variable for main thread
    thread_locks[__thread_id_main] = threading.Condition()

    # instantiate Threads and start them running
    create_worker_thread(streamers, __thread_id_livestreams)
    create_worker_thread(streamers, __thread_id_videos)
    create_worker_thread(streamers, __thread_id_followers)


    # main thread will dispatch worker threads forever
    while(1):

        # let main thread sleep until there is work to do
        # -> we don't actually need worker threads to wait on main thread's work, so release the lock immediately
        thread_locks[__thread_id_main].acquire()
        while (not check_if_main_should_awake()):
            thread_locks[__thread_id_main].wait()
        thread_locks[__thread_id_main].release()


        # If any threads have finished their work, save their results and restart them
        for thread_id in work:
            if (work[thread_id]['status'] == 'done'):

                thread_locks[thread_id].acquire()

                # save work done by thread
                streamers.merge(work[thread_id]['streamers'])
                streamers.export_to_csv(__streamers_folderpath)

                # log thread actions
                if (thread_id == __thread_id_videos):
                    streamers.known_missing_videos.export_to_csv(__streamers_missing_videos_filepath)
                work[thread_id]['request_logs'].export_to_csv(get_request_logs_filepath(), thread_id)
                if (thread_id == __thread_id_livestreams):
                    current_month = datetime.datetime.now().strftime("%Y-%m")
                    insights.set_month(current_month)
                    insights.set_data('streamers', streamers)
                    insights.get_snapshot_of_streamers_db()

                # reset the thread and get it ready to work
                work[thread_id]['streamers'] = streamers.clone()
                work[thread_id]['status'] = 'waiting'

                thread_locks[thread_id].notify_all()
                thread_locks[thread_id].release()



        # update any threads who can't do work because their streamers clone is expired
        for thread_id in work:
            if (work[thread_id]['status'] == 'needs_update'):
                work[thread_id]['streamers'] = streamers.clone()
                work[thread_id]['status'] = 'waiting'
                thread_locks[thread_id].acquire() # <- wake up the thread if its sleeping
                thread_locks[thread_id].notify_all()
                thread_locks[thread_id].release()

        # revive any threads that died -> THREADS NEVER DIE!
        for thread_id in worker_threads:
            if (not worker_threads[thread_id].is_alive()):
                create_worker_thread(streamers, thread_id)

# Run --------------------------------------------------------------------------

if (__name__ == '__main__'):
    main_thread()
