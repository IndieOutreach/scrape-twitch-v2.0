# IndieOutreach: Scrape

## About
This project scrapes content from the [Twitch](https://dev.twitch.tv/docs/api/reference#get-streams) and [IGDB](https://api-docs.igdb.com/?shell#age-rating) APIs and compiles them into a CSV file for future use.



## Installation
This scraping tool is built in Python 3.7.6 and uses the requests library for interfacing with the Twitch and IGDB APIs.

#### Instructions
 - Clone this repo
 - Create './credentials.json' with content: `{"twitch": "YOUR_TWITCH_CLIENT_ID", "igdb": "YOUR_IGDB_USER_KEY"}` so scraper.py can access the necessary APIs using your account info.

#### How to Run
 - run `python scraper.py` to run the scraper
 - run `python tests.py` to run the test suite and make sure all components of the scraper work


## Files

#### scraper.py
Used for scraping data from the Twitch API

#### tests.py
Testing script that checks functionality in scraper.py


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
 - `total_views` - the total number of views (different than the calculated number IndieOutreach will use)
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


## Development Notes

#### What is new in this commit?
 - Update README.md to specify raw data that scraper is scraping

#### What's next?
 - Add "streamer", "stream", and "game" classes

#### Future Roadmap
 - Clean the IGDB keyword data (so "boss battles" has 1 ID instead of 5 user inputted ones)
 - Compile the [keyword, genre, theme, platform] alias tables for IGDB
 - Scraping Algorithm
 - export to CSV
 - load from CSV
