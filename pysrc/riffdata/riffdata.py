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
from datetime import timedelta
from pymongo import MongoClient

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


# Just for expediency for now, everything is going in this file/module
# but this analysis really should go elsewhere eventually

def get_utterance_durations(meetings):
    """
    Get a list of the duration of all utterances from all meetings
    """
    durations = []

    for meeting_id in meetings:
        participant_uts = meetings[meeting_id]
        for participant_id in participant_uts:
            uts = participant_uts[participant_id]
            durations += [ut['duration'] for ut in uts]

    return durations


def _test():
    meetings = get_meetings_with_participant_utterances()

    print(f'Found utterances from {len(meetings)} meetings')
    meeting_ids = list(meetings)

    participant_uts = meetings[meeting_ids[0]]
    print(f'For the meeting with id {meeting_ids[0]}:')
    for participant_id in participant_uts:
        print(f'  participant id {participant_id} had {len(participant_uts[participant_id])} utterances')

    durations = get_utterance_durations(meetings)

    print(f'Found {len(durations)} utterances')

    durations.sort()

    print(f'shortest utterance was {durations[0]}ms and longest was {durations[-1]}ms')

    buckets = {'=0ms': 0,
               '2ms': 0,
               '5ms': 0,
               '10ms': 0,
               '100ms': 0,
               '500ms': 0,
               '2s': 0,
               '4s': 0,
               '6s': 0,
               '8s': 0,
               '10s': 0,
               '30s': 0,
               '1m': 0,
               '2m': 0,
               '>=2m': 0,
               }
    for duration in durations:
        if duration == 0:
            buckets['=0ms'] += 1
        elif duration < 2:
            buckets['2ms'] += 1
        elif duration < 5:
            buckets['5ms'] += 1
        elif duration < 10:
            buckets['10ms'] += 1
        elif duration < 100:
            buckets['100ms'] += 1
        elif duration < 500:
            buckets['500ms'] += 1
        elif duration < 2000:
            buckets['2s'] += 1
        elif duration < 4000:
            buckets['4s'] += 1
        elif duration < 6000:
            buckets['6s'] += 1
        elif duration < 8000:
            buckets['8s'] += 1
        elif duration < 10000:
            buckets['10s'] += 1
        elif duration < 30000:
            buckets['30s'] += 1
        elif duration < 60000:
            buckets['1m'] += 1
        elif duration < 120000:
            buckets['2m'] += 1
        else:
            buckets['>=2m'] += 1

    pprint.pprint(buckets)


if __name__ == '__main__':
    _test()
