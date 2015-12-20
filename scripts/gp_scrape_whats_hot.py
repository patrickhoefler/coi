# coding: utf-8

#
# Google+ What's Hot Scraper
#

__author__ = 'Patrick Hoefler'

from bs4 import BeautifulSoup
import datetime
import os
import re
import requests
import signal
import sys
import time
from pymongo import MongoClient


# Global constants and variables
DEBUG = True
shutdown_flag = False


def signal_handler(signal, frame):
    global shutdown_flag
    shutdown_flag = True


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Get connection to MongoDB
    connection = MongoClient(os.environ['MONGO_1_PORT_27017_TCP_ADDR'])
    db = connection.coi

    while True:
        scrape_whats_hot(db)

        for i in xrange(1800):
            global shutdown_flag
            if shutdown_flag:
                'Shutting down'
                sys.exit(0)
            time.sleep(1)


def scrape_whats_hot(db):
    global DEBUG

    r  = requests.get("https://plus.google.com/explore/_")
    soup = BeautifulSoup(r.text, 'html.parser')

    ids = set()

    for link in soup.find_all(href=re.compile('^\.?\/?\d+$')):
        ids.add(re.search('\d+', link.get('href')).group(0))

    # Get connection to MongoDB
    connection = MongoClient(os.environ['MONGO_1_PORT_27017_TCP_ADDR'])
    db = connection.coi

    for id in ids:
        db.cache_queue.update(
            {'_id': id},
            {
                '$setOnInsert':
                    {'crawl_not_before': datetime.datetime.utcnow()},
                '$inc': {'priority': 100},
            },
            upsert=True,
        )

    connection.close()


# Run the program from the command line
if __name__=='__main__':
  main()
