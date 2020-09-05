# Scrapers:
These are scrapers for a series of health forums for which the terms of service allow scraping. The read me items below will generally apply to every scraper, except where noted.

Scrapers

    sjogrensworld = sjogrensworld.org
    lupuscommunity = lupuscommunity.messageboardchat.com
    thelupussite = thelupussite.com


# Installation

Install requirements.txt `pip install -r requirements.txt`
and set mysql database connection information in settings.py, if you skip this, the sqlite database in the same folder will be created on the first run.

## MySQL Database installation

Make sure to create the database with a unicode character set `CREATE DATABASE mydb DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;`

## Default Database is Postgres

# example use

run `python main.py --scrape sjogrensworld`
