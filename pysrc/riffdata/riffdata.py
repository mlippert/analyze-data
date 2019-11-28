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

for participant in participants_cursor:
    pprint.pprint(participant)


# get all the meeting ids from the utterances (ie we don't want to depend on the
# meeting collection)

meeting_ids = db.utterances.distinct('meeting')

for meeting_id in meeting_ids:
    pprint.pprint(meeting_id)

# aggregate pipelines are probably going to be needed for something else
# pipeline = [
#     {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
#     {"$sort": SON([("count", -1), ("_id", -1)])}
# ]
# meeting_ids_cursor = db.utternances.aggregate(pipeline)
