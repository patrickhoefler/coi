# coding: utf-8

#
# Google+ Queue Existing Users
#

__author__ = 'Patrick Hoefler'

import datetime
import os
from pymongo import MongoClient
import signal
import sys
import time


# Global constants and variables
DEBUG = True
shutdown_flag = False


def signal_handler(signal, frame):
    global shutdown_flag
    shutdown_flag = True


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    global DEBUG

    # Get connection to MongoDB
    connection = MongoClient(os.environ['MONGO_1_PORT_27017_TCP_ADDR'])
    db = connection.coi

    while True:
        if DEBUG: print('Queueing users')
        queue_users(db)

        for i in xrange(60):
            global shutdown_flag
            if shutdown_flag:
                'Shutting down'
                sys.exit(0)
            time.sleep(1)


def queue_users(db):
    global DEBUG

    # Queue the 150 most popular users
    for person in db.statistics_activities.find({}).sort('score', -1).limit(150):

        db.cache_queue.update(
            {'_id': person['_id']},
            {'$set':
                {
                 'displayName': person['displayName'],
                 'crawl_not_before': person['updated'] + datetime.timedelta(hours=1),
                },
             '$inc': {'priority': 3},
            },
            True,
        )

    # Queue the users of the 150 most popular posts
    for post in db.statistics_posts.find({}).sort('score', -1).limit(150):

        db.cache_queue.update(
            {'_id': post['actorId']},
            {'$set':
                {
                 'displayName': post['actorDisplayName'],
                 'crawl_not_before': post['updated'] + datetime.timedelta(hours=1),
                },
             '$inc': {'priority': 2},
            },
            True,
        )

    # Additionally, queue the users of the 15 most popular posts of the last 24 hours
    for post in db.statistics_posts.find({'published': {'$gt': datetime.datetime.utcnow() - datetime.timedelta(hours=24)}}).limit(15):

        db.cache_queue.update(
            {'_id': post['actorId']},
            {'$set':
                {
                 'displayName': post['actorDisplayName'],
                 'crawl_not_before': post['updated'] + timedelta(hours=crawl_settings['recrawl_interval']),
                },
             '$inc': {'priority': 2},
            },
            True,
        )

    # Queue users with outdated posts
    for post in db.statistics_posts.find({'published': {'$lt': datetime.datetime.utcnow() - datetime.timedelta(7)}}):

        db.cache_queue.update(
            {'_id': post['actorId']},
            {'$set':
                {
                    'displayName': post['actorDisplayName'],
                    'crawl_not_before': post['updated'] + timedelta(hours=crawl_settings['recrawl_interval']),
                },
                '$inc': {'priority': 1},
            },
            True,
        )


# Run the program from the command line
if __name__=='__main__':
  main()
