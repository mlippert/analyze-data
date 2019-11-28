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

from pymongo import MongoClient
import pprint

dbDomain = 'localhost'
dbPort = 27017
dbName = 'riff-test'

# or
# mongo_uri: mongodb://localhost:27017/riff-test

client = MongoClient(dbDomain, dbPort)
db = client[dbName]

participantsCursor = db.participants.find()

for participant in participantsCursor:
    pprint.pprint(participant)


# get all the meeting ids from the utterances (ie we don't want to depend on the
# meeting collection)

meetingIds = db.utterances.distinct('meeting')

for meetingId in meetingIds:
    pprint.pprint(meetingId)

# aggregate pipelines are probably going to be needed for something else
# pipeline = [
#     {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
#     {"$sort": SON([("count", -1), ("_id", -1)])}
# ]
# meetingIdsCursor = db.utternances.aggregate(pipeline)
