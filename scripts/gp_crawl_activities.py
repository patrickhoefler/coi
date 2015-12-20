# coding: utf-8

#
# Google+ Activities Crawler
#

__author__ = 'Patrick Hoefler'

import apiclient.discovery
import apiclient.errors
import datetime
import httplib2
import json
import os
import signal
import sys
import time
import urllib
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
        crawl_person(db)

        for i in xrange(10):
            global shutdown_flag
            if shutdown_flag:
                'Shutting down'
                sys.exit(0)
            time.sleep(1)


def crawl_person(db):
    global DEBUG

    # How many days back should we go?
    archive_days = 7

    service = apiclient.discovery.build(
        'plus',
        'v1',
        http=httplib2.Http(),
        developerKey=os.environ['GOOGLE_API_KEY']
    )

    # Get the person with the highest crawl priority from the queue
    person = db.cache_queue.find_and_modify(
        query={'crawl_not_before': {'$lte': datetime.datetime.utcnow()}},
        sort={'priority': -1},
        remove=True,
    )

    if not person:
        return

    if person:
        try:
            activities_doc = service.activities().list(userId=person['_id'], collection='public').execute(httplib2.Http())
            if DEBUG: print("Successfully fetched some data for " + person['_id'])

        except ValueError:
            db.cache_log.insert({'error': 'ValueError', 'query_type': 'activities', 'person_id': person['_id'], 'time': datetime.datetime.utcnow()})
            if DEBUG:
                print("The data of " + person['_id'] + "was not valid JSON!")
            return

        except apiclient.errors.HttpError, err:
            db.cache_log.insert({'error': 'HttpError', 'message': str(err), 'query_type': 'activities', 'person_id': person['_id'], 'time': datetime.datetime.utcnow()})
            if DEBUG:
                print('HttpError: ' + str(err))
            return

        # Extract the activity items
        if activities_doc != None and activities_doc.get('items') and len(activities_doc.get('items')) > 0:
            activities = activities_doc['items']
            if DEBUG:
                print(str(len(activities)) + ' activities fetched.')
                print("Date of earliest activity: ", activities[-1]['published'])

            # Filter out all activities that are too old
            def find_relevant_activities(activity):
                return datetime.datetime.strptime(activity['published'], '%Y-%m-%dT%H:%M:%S.%fZ') > (datetime.datetime.utcnow() - datetime.timedelta(archive_days))

            if DEBUG: print('Unfiltered activity count: ' + str(len(activities)))
            activities = filter(find_relevant_activities, activities)
            if DEBUG: print('Filtered activity count: ' + str(len(activities)))

            # Are there any activities left?
            if len(activities) > 0:

                # Set the _id of the activities for MongoDB
                for activity in activities:
                    activity['_id'] = activity['id']

                # Remove the old activities of the user
                db.cache_activity.remove({'actor.id': person['_id']})

                # Save the new activities
                db.cache_activity.insert(activities)

                # Find new user IDs and queue them
                for activity in db.cache_activity.find({'actor.id': person['_id'], 'verb': 'share'}):
                    if 'actor' in activity['object']:
                        cache_data = db.cache_meta.find_one({'_id': activity['object']['actor']['id']})
                        if cache_data != None and 'crawl_not_before' in cache_data:
                            crawl_not_before = cache_data['crawl_not_before']
                        else:
                            crawl_not_before = datetime.datetime.utcnow()

                        db.cache_queue.update(
                            {'_id': activity['object']['actor']['id']},
                            {
                                '$set':
                                    {
                                        'displayName': activity['object']['actor']['displayName'],
                                        'crawl_not_before': crawl_not_before,
                                    },
                                '$inc': {'priority': 3},
                            },
                            upsert=True,
                        )

                # Update the meta info
                db.cache_meta.update(
                    {'_id': person['_id']},
                    {'displayName': activities[0]['actor']['displayName']},
                    upsert=True,
                )

                # Calculate the statistics
                score_per_day = {}
                score_per_hour = {}

                # Iterate over the archive days + today
                def daterange(start_date, end_date):
                    for n in range((end_date - start_date).days):
                        yield start_date + datetime.timedelta(n)

                for single_date in daterange(datetime.date.today() - datetime.timedelta(archive_days), datetime.date.today() + datetime.timedelta(1)):
                    day = time.strftime("%Y-%m-%d", single_date.timetuple())
                    score_per_day[day] = 0

                # Iterate over the last 24 hours + the current hour
                def hour_range(start_date, end_date):
                    for n in range(int((end_date - start_date).total_seconds() / 3600)):
                        yield start_date + datetime.timedelta(hours=n)

                for single_hour in hour_range(datetime.datetime.utcnow() - datetime.timedelta(hours=24), datetime.datetime.utcnow() + datetime.timedelta(hours=1)):
                    hour = time.strftime("%Y-%m-%d %H", single_hour.timetuple())
                    score_per_hour[hour] = 0

                # Crunch some numbers
                score = 0
                score_24 = 0

                for activity in db.cache_activity.find({'actor.id': person['_id']}).sort('published'):

                    day = time.strftime("%Y-%m-%d", time.strptime(activity['published'], '%Y-%m-%dT%H:%M:%S.%fZ'))
                    hour = time.strftime("%Y-%m-%d %H", time.strptime(activity['published'], '%Y-%m-%dT%H:%M:%S.%fZ'))

                    if day in score_per_day:
                        post_score  =     activity['object']['plusoners']['totalItems']
                        post_score += 2 * activity['object']['replies']['totalItems']
                        post_score += 3 * activity['object']['resharers']['totalItems']

                        score += post_score
                        score_per_day[day] += post_score

                        if datetime.datetime.strptime(activity['published'], '%Y-%m-%dT%H:%M:%S.%fZ') > (datetime.datetime.utcnow() - datetime.timedelta(days=1)):
                            score_24 += post_score
                            score_per_hour[hour] += post_score

                score_list = []
                score_list_24 = []

                for day in sorted(score_per_day):
                    score_list.append(score_per_day[day])

                for hour in sorted(score_per_hour):
                    score_list_24.append(score_per_hour[hour])


                db.statistics_activities.update(
                    {'_id': person['_id']},
                    {'$set':
                        {
                         'displayName': activity['actor']['displayName'],
                         'image': activity['actor']['image']['url'],
                         'score_list': score_list,
                         'score_list_24': score_list_24,
                         'score': int(score),
                         'score_24': int(score_24),
                         'updated': datetime.datetime.utcnow(),
                        },
                    },
                    True,
                )


                # Calculate the post statistics
                for activity in db.cache_activity.find({'actor.id': person['_id']}):

                    score  =     activity['object']['plusoners']['totalItems']
                    score += 2 * activity['object']['replies']['totalItems']
                    score += 3 * activity['object']['resharers']['totalItems']

                    # Convert 'published' string into datetime
                    published = datetime.datetime.strptime(activity['published'], '%Y-%m-%dT%H:%M:%S.%fZ')

                    # Set the content of the post
                    if activity['verb'] == 'share':
                        content = activity.get('annotation')
                    else:
                        content = activity['object']['content']

                    # Set an image for the post
                    if 'attachments' in activity and 'image' in activity['attachments'][0]:
                        image = activity['attachments'][0]['image']['url']
                    elif 'attachments' in activity and len(activity['attachments']) > 1:
                        image = activity['attachments'][1]['image']['url']
                    elif 'attachments' in activity['object'] and 'image' in activity['object']['attachments'][0]:
                        image = activity['object']['attachments'][0]['image']['url']
                    elif 'attachments' in activity['object'] and len(activity['object']['attachments']) > 1:
                        image = activity['object']['attachments'][1]['image']['url']
                    else:
                        image = ''

                    db.statistics_post.update(
                        {'_id': activity['id']},
                        {'$set':
                            {
                             'title': activity['title'],
                             'content': content,
                             'image': image,
                             'url': activity['url'],
                             'actorId': person['_id'],
                             'actorDisplayName': activity['actor']['displayName'],
                             'actorImage': activity['actor']['image']['url'],
                             'published': published,
                             'number_of_plusoners': activity['object']['plusoners']['totalItems'],
                             'number_of_replies': activity['object']['replies']['totalItems'],
                             'number_of_resharers': activity['object']['resharers']['totalItems'],
                             'score': int(score),
                             'updated': datetime.datetime.utcnow(),
                            },
                        },
                        True,
                    )


            else:
                # Since there are no relevant activities anymore, remove the activities statistics for the person
                db.statistics_activities.remove(
                    {
                     'actorId': person['_id'],
                    }
                )


        # Remove old post statistics
        db.statistics_post.remove(
            {
             'actorId': person['_id'],
             'updated': {'$lt': datetime.datetime.utcnow() - datetime.timedelta(minutes=1)}
            }
        )

        # Make sure that we don't crawl the same person over and over again
        db.cache_meta.update(
            {'_id': person['_id']},
            {'$set':
                {
                    'crawl_not_before': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                },
            },
            True,
        )


# Run the program from the command line
if __name__=='__main__':
  main()
