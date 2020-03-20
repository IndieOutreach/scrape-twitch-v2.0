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

### tests.py
Testing script that checks functionality in scraper.py

## Development Notes

#### What is new in this commit?
 - Add IGDBAPI to scraper.py with function .search_for_game_by_name()

#### What's next?
 - Add "streamer", "stream", and "game" classes

#### Future Roadmap
 - Clean the IGDB keyword data (so "boss battles" has 1 ID instead of 5 user inputted ones)
 - Compile the [keyword, genre, theme, platform] alias tables for IGDB
 - Scraping Algorithm
 - export to CSV
 - load from CSV
