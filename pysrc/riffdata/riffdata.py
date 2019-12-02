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
import matplotlib.pyplot as plt
import numpy as np

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


def my_plotter(ax, data1, data2, param_dict):
    """
    A helper function to make a graph

    Parameters
    ----------
    ax : Axes
        The axes to draw to

    data1 : array
       The x data

    data2 : array
       The y data

    param_dict : dict
       Dictionary of kwargs to pass to ax.plot

    Returns
    -------
    out : list
        list of artists added
    """
    out = ax.plot(data1, data2, **param_dict)
    return out


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

    buckets = [0, 2, 5,                         #   0 -   2
               *range(10, 300, 10),             #   3 -  32
               *range(300, 3500, 50),           #  33 -  96
               *range(3500, 8001, 500),         #  97 - 106
               *range(10000, 60001, 10000),     # 107 - 113
              ]

    bucket_cnt = [0]
    bucket_ndx = 0
    for duration in durations:
        if bucket_ndx >= len(buckets) or duration <= buckets[bucket_ndx]:
            bucket_cnt[bucket_ndx] += 1
            continue

        bucket_ndx += 1
        while bucket_ndx < len(buckets) and duration > buckets[bucket_ndx]:
            bucket_cnt.append(0)
            bucket_ndx += 1

        bucket_cnt.append(1)

    for i in range(0, len(bucket_cnt) - 1):
        print(f'{timedelta(milliseconds=buckets[i])}: {bucket_cnt[i]}')

    print(f'>: {bucket_cnt[len(bucket_cnt) - 1]}')

    graph_ranges = [1, 33, 97, 107]

    def _make_xy_sets_to_plot(x_src, y_src, ranges):
        # must have at least 2 indices in ranges, not checking for that yet
        x = []
        y = []
        start = ranges[0]
        for end in ranges[1:]:
            x.append(np.array(x_src[start:end]))
            y.append(np.array(y_src[start:end]))
            start = end

        return x, y

    x, y = _make_xy_sets_to_plot(x_src=buckets, y_src=bucket_cnt, ranges=graph_ranges)

    fig, ax = plt.subplots(len(x), 1)
    for plot in range(0, len(x)):
        my_plotter(ax[plot], x[plot], y[plot], {'marker': 'x'})

    fig.savefig('plot.png')


if __name__ == '__main__':
    _test()
