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
import logging
import pprint
from datetime import timedelta

# Third party imports
from pymongo import MongoClient

# Local application imports

default_domain = 'localhost'
default_port = 27017
default_db_name = 'riff-test'

# or
# mongo_uri: mongodb://localhost:27017/riff-test

client = MongoClient(default_domain, default_port)
db = client[default_db_name]


class Riffdata:
    """
    An instance of Riffdata is created with the MongoDb
    domain, port and db name of the riffdata database to
    be queried.

    The methods will return information from that database.

    Information can be returned about:

    - meetings
    - utterances
    - participants
    """

    # format strings for the objects returned by Riffdata methods
    meeting_fmt = ('meeting ({_id}) in room {room}\n'
                   '{startTime:%Y %b %d %H:%M} — {endTime:%H:%M} ({meetingLengthMin:.1f} minutes)\n'
                   '{participant_cnt} participants:'
                  )

    def __init__(self, *, domain=default_domain, port=default_port, db_name=default_db_name):
        """
        """
        self.logger = logging.getLogger('riffAnalytics.Riffdata')

        self._domain = domain
        self._port = port
        self._db_name = db_name
        self.client = MongoClient(self._domain, self._port)
        self.db = self.client[self._db_name]

    def get_meetings(self, pre_query=None, post_query=None):
        """
        Get all of the meetings from the riffdata mongodb meetings collection.

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

        meetings_cursor = self.db.meetings.aggregate(pipeline, allowDiskUse=True)
        # meetings_cursor = db.meetings.find(pre_query)
        for meeting in meetings_cursor:
            meetings.append(meeting)
        return meetings

    def get_meeting(self, meeting_id):
        qry = {'_id': meeting_id}
        meetings = self.get_meetings(qry)
        # TODO how to handle meeting not found?!
        meeting = meetings[0]

        qry = {'meeting': meeting_id}
        utterance_cursor = self.db.utterances.find(qry)
        meeting['participant_uts'] = Riffdata._group_utterances(utterance_cursor)[meeting_id]

        return meeting

    def get_participants(self):
        """
        Get all of the participants from the riffdata mongodb participants collection.
        """
        participants = []
        participants_cursor = self.db.participants.find()
        for participant in participants_cursor:
            participants += participant
            pprint.pprint(participant)
        return participants

    def get_meetings_with_participant_utterances(self):
        """
        Return a dict indexed by meeting id to a dict indexed by participant id
        of a list of all utterances by that participant in that meeting.
        Each utterance is a dict of start, end and duration of an utterance by
        the participant in the meeting.
        { <meeting_id>: {<participant_id>: [{start: Date, end: Date, duration: integer}], ...}, ...}
        """
        utterance_cursor = self.db.utterances.find()
        meetings = Riffdata._group_utterances(utterance_cursor)

        return meetings

    @staticmethod
    def _group_utterances(utterance_cursor):
        """
        Group all the utterances from the cursor by meeting id and then by
        participant id
        """
        meetings = {}
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

    @staticmethod
    def print_meeting(meeting):
        """
        Print the meeting.
        """
        print(Riffdata.meeting_fmt.format(**meeting, participant_cnt=len(meeting['participants'])))

        i = 0
        if 'participant_uts' in meeting:
            participant_uts = meeting['participant_uts']
            participants = {p: 0 for p in meeting['participants']}
            for p in participant_uts:
                participants[p] = len(participant_uts[p])

            for p in participants:
                i += 1
                print(f'  {i:2}) {p} made {participants[p]} utterances')
        else:
            for p in meeting['participants']:
                i += 1
                print(f'  {i:2}) {p}')


    # ## Methods under construction/consideration ##

    def get_all_meetings_from_utterances(self):
        """
        get all the meeting ids from the utterances (ie we don't want to depend on the
        meeting collection)
        """
        meeting_ids = self.db.utterances.distinct('meeting')

        for meeting_id in meeting_ids:
            pprint.pprint(meeting_id)

    # WIP TODO
    # compute the following:
    # for each participant
    #   array of lengths in ms of their utterances
    #   array of lengths in ms of gap between one of their utterances in a meeting and their next utterance

    # since we need both of the above, we should group the utterances by meeting
    # which will allow traversing the utterances once.

    def get_meetings_with_utterances_using_mongo_aggregate(self):
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

        meeting_utterances_cursor = self.db.utterances.aggregate(pipeline, allowDiskUse=True)

        max_utterances = 0
        for meeting_utterances in meeting_utterances_cursor:
            print(f'meeting ID: {meeting_utterances["_id"]}\n'
                  f'  # of utterances: {meeting_utterances["count"]}\n'
                  f'  # of participants: {len(meeting_utterances["participantIds"])}'
                 )
            if max_utterances < meeting_utterances['count']:
                max_utterances = meeting_utterances['count']

        print(f'Most utterances in a meeting was {max_utterances}\n')


def _test():
    pass


if __name__ == '__main__':
    _test()
