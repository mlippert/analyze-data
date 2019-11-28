#################################################################################
# riffdata.py                                                                   #
#################################################################################
#
# The riffdata module retrieves the raw riffdata from the database
#
# Created on    November 27, 2019
# author        Michael Jay Lippert
#
# (c) 2019-present Riff Learning Inc.,
# MIT License (see https://opensource.org/licenses/MIT)
#
#################################################################################

import pprint
from pymongo import MongoClient

dbDomain = 'localhost'
dbPort = 27017
dbName = 'riff-test'

# or
# mongo_uri: mongodb://localhost:27017/riff-test

client = MongoClient(dbDomain, dbPort)
db = client[dbName]

participants_cursor = db.participants.find()

# for participant in participants_cursor:
#     pprint.pprint(participant)


# get all the meeting ids from the utterances (ie we don't want to depend on the
# meeting collection)

meeting_ids = db.utterances.distinct('meeting')

#for meeting_id in meeting_ids:
#    pprint.pprint(meeting_id)

# aggregate pipelines are probably going to be needed for something else
# pipeline = [
#     {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
#     {"$sort": SON([("count", -1), ("_id", -1)])}
# ]
# meeting_ids_cursor = db.utterances.aggregate(pipeline)


# compute the following:
# for each participant
#   array of lengths in ms of their utterances
#   array of lengths in ms of gap between one of their utterances in a meeting and their next utterance

# since we need both of the above, we should group the utterances by meeting
# which will allow traversing the utterances once.

pipeline = [{'$group': {'_id': '$meeting',
                        'count': {'$sum': 1},
# this creates a field that is too big
# pymongo.errors.OperationFailure: BSONObj size: 34829138 (0x2137352) is invalid.
#                                  Size must be between 0 and 16793600(16MB) First element: _id: null
# From https://forums.meteor.com/t/how-to-solve-group-mongo-with-document-16mb/47605/2
#   To my knowledge each property in a mongo document has a 16mb limit.
#                        'utterances': {'$push': {'participantId': '$participant',
#                                                 'startTime': '$startTime',
#                                                 'endTime': '$endTime',
#                                                 'duration': {'$subtract': ['$endTime', '$startTime']},
#                                                }
#                                      },
                        'participantIds': {'$addToSet': '$participant'},
                       }
            },
           ]

meeting_utterances_cursor = db.utterances.aggregate(pipeline, allowDiskUse=True)

max_utterances = 0
for meeting_utterances in meeting_utterances_cursor:
    print(f'meeting ID: {meeting_utterances["_id"]}\n'
          f'  # of utterances: {meeting_utterances["count"]}\n'
          f'  # of participants: {len(meeting_utterances["participantIds"])}'
         )
    if (max_utterances < meeting_utterances['count']):
        max_utterances = meeting_utterances['count']

print(f'Most utterances in a meeting was {max_utterances}\n')
