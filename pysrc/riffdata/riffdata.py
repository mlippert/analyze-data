"""
################################################################################
  riffdata.riffdata.py
################################################################################

The riffdata module retrieves the raw riffdata from the database

=============== ================================================================
Created on      November 27, 2019
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2019-present Riff Learning Inc.,
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
import pprint
from datetime import timedelta, datetime
from functools import reduce

# Third party imports
from pymongo import MongoClient

# Local application imports

dbDomain = 'localhost'
dbPort = 27017
dbName = 'riff-test'

# or
# mongo_uri: mongodb://localhost:27017/riff-test

client = MongoClient(dbDomain, dbPort)
db = client[dbName]


def get_participants():
    participants = []
    participants_cursor = db.participants.find()
    for participant in participants_cursor:
        participants += participant
        pprint.pprint(participant)
    return participants


def get_meetings(pre_query=None, post_query=None):
    """
    Get all of the meetings from the riffdata mongodb in the meetings collection.

    Adds some calculated fields to the fields of the meeting document and removes
    some irrelevant fields.

    The returned list may be filtered by specifying a pre and/or post query using
    MongoDb `query syntax <https://docs.mongodb.com/manual/reference/operator/query/>`_.

    :param pre_query: A mongo query for the meetings collection that can use any
                      of the fields in the meeting document. This query filters
                      out meetings before the pipeline adds calculated fields
    :type pre_query: dict

    :param post_query: A mongo query for the meetings collection that can use any
                       of the fields in the meeting document AND any of the added
                       calculated fields. This query filters out meetings after
                       the pipeline adds calculated fields
    :type post_query: dict

    :return: A list of all matching meetings where a meeting is a dict with the
             following keys:
             - '_id': str - the unique meeting id
             - 'startTime': datetime - time the meeting started
             - 'endTime': datetime - time the meeting ended
             - 'room': str - name of the room used for the meeting
             - 'meetingLengthMin': float - calculated length of the meeting in minutes
             - 'participants': list of participant ids (strs) who attended the meeting
    """
    meetings = []
    pipeline = [
        {'$addFields': {'meetingLengthMin': {'$divide': [{'$subtract': ['$endTime', '$startTime']}, 60000]}
                       }
        },
        {'$lookup': {'from': 'participantevents',
                     'localField': '_id',
                     'foreignField': 'meeting',
                     'as': 'participantevents'
                    }
        },
        {'$addFields': {'participants': {'$setUnion': {'$reduce': {'input': '$participantevents.participants',
                                                                   'initialValue': [],
                                                                   'in': {'$concatArrays':
                                                                            ['$$value', '$$this']
                                                                         }
                                                                  }
                                                      }
                                        }
                       }
        },
        {'$project': {'startTime': True,
                      'endTime': True,
                      'meetingLengthMin': True,
                      'participants': True,
                      'room': True,
                     }
        },
    ]

    if pre_query is not None:
        # Add query as an initial match stage to the aggregate pipeline
        pipeline[0:0] = [{'$match': pre_query}]

    if post_query is not None:
        # Add query as a final match stage to the aggregate pipeline
        pipeline.append({'$match': post_query})

    meetings_cursor = db.meetings.aggregate(pipeline, allowDiskUse=True)
    # meetings_cursor = db.meetings.find(pre_query)
    for meeting in meetings_cursor:
        meetings.append(meeting)
    return meetings


def get_all_meetings_from_utterances():
    """
    get all the meeting ids from the utterances (ie we don't want to depend on the
    meeting collection)
    """
    meeting_ids = db.utterances.distinct('meeting')

    for meeting_id in meeting_ids:
        pprint.pprint(meeting_id)


# compute the following:
# for each participant
#   array of lengths in ms of their utterances
#   array of lengths in ms of gap between one of their utterances in a meeting and their next utterance

# since we need both of the above, we should group the utterances by meeting
# which will allow traversing the utterances once.


def get_meetings_with_utterances_using_mongo_aggregate():
    """
    This didn't work as intended because (however it is still good example code for now):
    The 'utterances' field in this aggregate pipeline $group stage is too big
    which is why it is commented out.
    pymongo.errors.OperationFailure: BSONObj size: 34829138 (0x2137352) is invalid.
                                     Size must be between 0 and 16793600(16MB)
                                     First element: _id: null
    From https://forums.meteor.com/t/how-to-solve-group-mongo-with-document-16mb/47605/2
      To my knowledge each property in a mongo document has a 16mb limit.
    """
    pipeline = [{'$group': {'_id': '$meeting',
                            'count': {'$sum': 1},
                            # 'utterances': {'$push': {'participantId': '$participant',
                            #                          'startTime': '$startTime',
                            #                          'endTime': '$endTime',
                            #                          'duration': {'$subtract': ['$endTime', '$startTime']},
                            #                         }
                            #               },
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
        if max_utterances < meeting_utterances['count']:
            max_utterances = meeting_utterances['count']

    print(f'Most utterances in a meeting was {max_utterances}\n')


def get_meetings_with_participant_utterances():
    """
    Return a dict indexed by meeting id to a dict indexed by participant id
    of a list of all utterances by that participant in that meeting.
    Each utterance is a dict of start, end and duration of an utterance by
    the participant in the meeting.
    { <meeting_id>: {<participant_id>: [{start: Date, end: Date, duration: integer}], ...}, ...}
    """
    meetings = {}
    utterance_cursor = db.utterances.find()
    for u in utterance_cursor:
        # I think this is a bug, but there are utterances w/o a meeting field, we will
        # just skip them
        if 'meeting' not in u:
            continue

        meeting_id = u['meeting']
        if meeting_id not in meetings:
            meetings[meeting_id] = {}
        participant_uts = meetings[meeting_id]

        participant_id = u['participant']
        if participant_id not in participant_uts:
            participant_uts[participant_id] = []
        uts = participant_uts[participant_id]

        ut = {'start': u['startTime'],
              'end': u['endTime'],
              'duration': (u['endTime'] - u['startTime']) // timedelta(milliseconds=1),
             }
        uts.append(ut)

    return meetings


def _test():
    pass

    qry = {'startTime': {'$gte': datetime(2019, 9, 11),
                         '$lt': datetime(2019, 12, 4),
                        }
          }
    meetings = get_meetings(qry)
    print(f'Ttoal number of meetings was {len(meetings)}\n')
    # pprint.pprint(meetings[0])

    def inc_cnt(d, key):
        if key in d:
            d[key] += 1
        else:
            d[key] = 1
        return d

    meetings_w_num_participants = reduce(inc_cnt, [len(meeting['participants']) for meeting in meetings], {})
    print('Number of meetings grouped by number of participants:')
    pprint.pprint(meetings_w_num_participants)

    meetings = [meeting for meeting in meetings if len(meeting['participants']) > 1]
    print(f'Number of meetings with more than 1 participant was {len(meetings)}\n')

    meeting_duration_distribution = [
        [5, 0],
        [10, 0],
        [20, 0],
        [40, 0],
        [60, 0],
        [120, 0],
        [180, 0],
        [720, 0],
    ]

    def inc_bucket(buckets, v):
        for b in buckets:
            if b[0] > v:
                b[1] += 1
                break
        return buckets

    meeting_durations = [meeting['meetingLengthMin'] for meeting in meetings]
    reduce(inc_bucket, meeting_durations, meeting_duration_distribution)
    pprint.pprint(meeting_duration_distribution)

    longest_meeting = max(meetings, key=lambda m: m['meetingLengthMin'])
    pprint.pprint(longest_meeting)

    avg_meeting_duration = sum(meeting_durations) / len(meeting_durations)
    print(f'Average length of a meeting was {(avg_meeting_duration + 0.5)//1} minutes\n')

    # find the set of unique participants in these meeting
    all_meeting_participants = set().union(*[meeting['participants'] for meeting in meetings])
    print(f'Total number of participants in these meetings was {len(all_meeting_participants)}\n')


if __name__ == '__main__':
    _test()
