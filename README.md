# IndieOutreach: Scrape

## About
This project scrapes content from the [Twitch](https://dev.twitch.tv/docs/api/reference#get-streams) and [IGDB](https://api-docs.igdb.com/?shell#age-rating) APIs and compiles them into a CSV file for future use.



## Installation
This scraping tool is built in Python 3.7.6 and uses the requests library for interfacing with the Twitch and IGDB APIs.

#### Instructions
 - Clone this repo
 - Create your own `./credentials.json` (format specified below) so scraper.py can access the necessary APIs using your account info.

#### pip installations
 - `requests-oauthlib` for making OAuth2 requests to Twitch's API

#### How to Run
 - run `python tests.py` to run the test suite and make sure all components of the scraper work
 - run `python scraper.py {flags}` to run the scraper. See section below about flag options



## Folders and Files

#### scraper.py
Used for scraping data from the Twitch and IGDB APIs

Flags:
 - `-g` or `--games`: uses the IGDB API to compile all games from IGDB into '/data/games.csv'
 - `-s` or `--streamers`: use the Twitch API to scrape all livestreams on Twitch, search for streamer profiles, and use that to build '/data/streamers.csv'
  - this option will also add 'twitch_box_art_url' to Games from '/data/games.csv' where necessary
  - this option will add Twitch->IGDB ID conversions as well

#### tests.py
Testing script that checks functionality in scraper.py

#### games.py
Contains the Games() and Game() classes

#### streamers.py
Contains the Stream(), Streamer(), and Streamers() classes

#### credentials.py
credentials.py holds API credentials for both Twitch and IGDB
Format:
 -  `{"twitch": {"client_id": "YOUR_APPS_CLIENT_ID", "client_secret": "YOUR_APPS_CLIENT_SECRET", "v5_client_id": "A_CLIENT_ID_FOR_V5_API"}, "igdb": "YOUR_IGDB_USER_KEY"}`
  - Note: the v5 API has been deprecated, so it may not be possible to get a new key that works for v5_client_id

#### /data
Folder contains all the .csv files that scraper compiles

#### /test_csv_output
Folder contains all the .csv files that are generated during testing

## Raw Data
Data that is scraped and used or stored.

#### Stream -> (no csv file)
A stream is a livestream or video.
We treat videos as if they are just livestreams we missed
 - `id` - unique Twitch ID for this stream
 - `user_id` - unique Twitch ID for the streamer  
 - `game_id` - unique Twitch ID for the game played
 - `language` - language the stream was broadcasted in
 - `date` - the time that this stream originally started broadcasting (converted to unix epochs)
 - `views` - number of views the stream has, videos don't count for views


 Note: Streams are not permanently recorded. Their information is stored into a Streamer and is then discarded.


#### Game -> games.csv
Info about a game from IGDB
 - `id` - unique IGDB ID for the game
 - `name` - the name of the game
 - `genres` - a list of genre IDs
 - `keywords` - a list of keyword IDs
 - `themes` - a list of theme IDs
 - `platforms` - a list of platform IDs
 - `rating` - rating of the game out of 100
 - `collection` - series of games it belongs to
 - `release_date` - date it was initially launched
 - `game_modes` - list of game mode IDs (single player, co-op, etc)
 - `player_perspectives` - list of perspectives the player plays in
 - `popularity` - popularity of the game (x/10)
 - `similar_games` - list of similar games, bu IGDB game IDs
 - `time_to_beat` - how long it takes to beat the game
 - `age_ratings` - list of rating IDs
 - `category` - int denoting what category of game this is (main, dlc, etc)
 - `igdb_box_art_url` - URL for game's box art from IGDB
 - `twitch_box_art_url` - URL for game's box art from Twitch

#### Streamer -> streamers.csv
Streamer profiles

Data from Twitch API:
 - `id` - unique Twitch user ID
 - `display_name`- the streamer's name
 - `profile_image_url` - the streamer's profile picture
 - `total_views` - A list of `{views: # views, date: UNIX_EPOCH_TIME}` objects. These objects represent the total number of views a streamer has at certain dates (different than the calculated number IndieOutreach will use)
 - `description` - user's bio
 - `num_followers` - number of followers this streamer has

Data aggregated from streams:
 - `stream_history` - a JSON object of format `{twitch_game_id: {times_played: 12, views: 123, num_videos: 1, dates: [timestamps...]}, ....}`
  - Note: views does not include the views on videos, so you'd have to to account for this when calculating average views
 - `language` - this value is just whatever the last processed stream's language was


#### Twitch To IGDB -> twitch_to_igdb.csv
Lookup table that maps {twitch_id: igdb_id} or {twitch_name: igdb_id}
 - `twitch_id` -  the ID of the game on twitch
 - `twitch_name` - the name specified on Twitch
 - `igdb_id` - the ID of the game on IGDB

#### IGDB Lookup Tables -> various
Lookup tables that map { igdbID: name }
 - keywords.csv
 - themes.csv
 - genres.csv
 - platforms.csv
 - collections.csv
 - categories.csv
 - age_ratings.csv
 - game_modes.csv
 - player_perspectives.csv


## Logs
Keeps track of actions and requests made by scraper.py

#### Runtime of Scraping Procedures-> runtime.csv
 - `time_started` - the unix epoch date (in milliseconds) that the procedure started on. This serves as a unique ID  
 - `time_ended` - the unix epoch date (in milleseconds) that the procedure ended on
 - `content_type` - The type of content that was scraped during procedure
  - Value is a string from list ['streamers', 'games', 'followers', 'videos']
 - `logs` - an object with the stats about the procedure's runtime
  - of form: `{ action_type: {'n': NUM_REQUESTS, 'total': TOTAL_TIME_TAKEN, 'mean': MEAN_TIME_PER_REQUEST, 'std_dev': STD_DEV_OF_TIME_PER_REQUEST, 'min': MIN_TIME_FOR_A_REQUEST, 'max': MAX_TIME_FOR_A_REQUEST, 'first_start': UNIX_EPOCH_TIMESTAMP_OF_WHEN_FIRST_REQUEST_STARTED, 'last_end': UNIX_EPOCH_TIMESTAMP_OF_WHEN_LAST_REQUEST_ENDED}, ... }`

## Development Notes

#### What is new in this commit?
- Remove streamer.last_updated

#### What is still in development? Known Issues?
 - the function check_if_streamer_collection_same() in streamers.py is a *mess* readability wise
 - modify stream_history[game_id]['dates'] to be a list of {'streamed', 'scraped'} objects instead of just streamed
 - add logic so stream_history records livestreams that have already been recorded but the game_id has switche

#### What's next?
 - convert streamer.num_followers into a list of follower counts [ {'date', 'followers'}, ... ]
 - tests.py output is cluttered due to printing non-test info at runtime in scraper.py
  - Convert scraper.py into a class and add a `silent_mode` feature?
 - Add scraper.add_videos_to_streamers_db()
 - Add scraper.add_followers_to_streamers_db()
 - create a TwitchToIGDB conversion table that converts game_names / twitch_game_ids to IGDB IDs


#### Future Roadmap
 - Clean the IGDB keyword data (so "boss battles" has 1 ID instead of 5 user inputted ones)
 - Compile the [keyword, genre, theme, platform] alias tables for IGDB
 - Modify scraper.compile_games_db() so it can take in a CSV file and not search for games it already has
 - convert tests.py to use argparse for consistency
 - move TimeLogs over to its own file timelogs.py and add functions for calculating stats from those logs
