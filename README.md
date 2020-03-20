# IndieOutreach: Scrape

## About
This project scrapes content from the [Twitch](https://dev.twitch.tv/docs/api/reference#get-streams) and [IGDB](https://api-docs.igdb.com/?shell#age-rating) APIs and compiles them into a CSV file for future use.

In its current state, it is just a README!


## Installation
This scraping tool is built in Python 3.7.6 and uses the requests library for interfacing with the Twitch and IGDB APIs.

Instructions
 - Clone this repo


## Files

#### twitch_scraper
Used for scraping data from the Twitch API

## Development Notes

### What is new in this commit?
 - created scraper.py
  - Add TwitchAPI class for handling API requests to Twitch (get_streams, get_user, get_followers, get_games, get_videos)
  - Add main function that will act as the main runner function for scraping content (both Twitch and IGDB)

 - created tests.py
  - Add tests for each of the TwitchAPI calls

### What's next?
 - Add IGDBAPI for scraping the IGDB API
 - Add "streamer", "stream", and "game" classes

### Future Roadmap
 - Clean the IGDB keyword data (so "boss battles" has 1 ID instead of 5 user inputted ones)
