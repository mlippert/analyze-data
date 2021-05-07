"""
################################################################################
  visualize.meetings.py
################################################################################

This module produces a visualization of the meetings over a given time period

=============== ================================================================
Created on      December 15, 2019
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2019-present Michael Jay Lippert,
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
import sys
from functools import reduce
from datetime import datetime, timedelta
from typing import (Any,
                    Iterable,
                    Mapping,
                    MutableMapping,
                    MutableSequence,
                    Sequence,
                    Set,
                    Tuple,
                    TypeVar,
                    Union,
                   )
from numbers import Real
from enum import Enum

# Local application imports
from riffdata.riffdata import Riffdata


# Generic type variable for defining function parameters
T = TypeVar('T')


class RoomDetailLevel(Enum):
    """
    Enumeration of levels of room detail that can be requested to be printed for
    the list of meetings that are being analyzed.
    """
    NONE = 'none'
    COUNT = 'count'
    SUMMARY = 'summary'
    SUMMARY_ATTENDEES = 'summary-attendees'
    ALL_MEETINGS = 'all-meetings'


def inc_cnt(d: MutableMapping[T, int], key: T) -> MutableMapping[T, int]:
    """
    reduce predicate that increments d[key], creating that key and
    setting it to 1 if it doesn't exist.

    Use it to count keys for example:
      # count the number of meetings with a particular count of participants from the list of meetings
      counts = reduce(inc_cnt, [len(meeting['participants']) for meeting in meetings], {})
    """
    if key in d:
        d[key] += 1
    else:
        d[key] = 1
    return d


def inc_bucket(buckets: Iterable[MutableSequence[Real]], v: Real) -> Iterable[MutableSequence[Real]]:
    """
    Given a sorted list of bucket counts where a bucket's 1st element is the
    bucket max value and the 2nd element is the count for that bucket
    Iterate the buckets to find the bucket where the given value v is less
    than the bucket max value, and increment that bucket count.

    Intended for use as a reduce predicate where the initial set of buckets
    have a count of 0.

    TODO: Allow a bucket w/ a max value of None which is always incremented
          when reached. Intended to be the final bucket to count values that
          didn't fall into any previous buckets (unless there is a better way
          to do this).
    """
    for b in buckets:
        if v < b[0]:
            b[1] += 1
            break
    return buckets


def write_buckets(buckets: Iterable[Sequence[Any]], *, f=sys.stdout) -> None:
    prev_b: Union[Sequence[Any], None] = None
    for b in buckets:
        if prev_b is None:
            f.write(f'  {"":4} < {b[0]:4}: {b[1]:4}\n')
        else:
            f.write(f'  {prev_b[0]:4} - {b[0]:4}: {b[1]:4}\n')
        prev_b = b


class MeetingsData:
    """
    Information about a set of meetings read from a Riffdata database
    """

    def __init__(self, riffdata, meeting_date_range: Tuple[datetime, datetime]) -> None:
        """
        Initialize the MeetingsData instance from the data in the given Riffdata database
        """
        # TODO: using UNKNOWN until the information is available -mjl 2020-07-10
        self.site = 'UNKNOWN'

        # request_period defines the meeting data retrieved and analyzed
        self.request_period = {'start': meeting_date_range[0],
                               'end': meeting_date_range[1],
                              }

        # initialize the meeting_stats, rooms, meetings for no meetings
        self.meeting_stats = {'total_meetings':         0,
                              'real_meetings':          0,  # meetings w/ more than 1 participant
                              'avg_meeting_length':     0,  # avg length of real meetings
                              'total_num_participants': 0,  # number of unique participants in real meetings
                             }
        self.rooms = []
        self.meetings = []
        self.meetings_by_room = {}

        db_meetings = self._get_db_meetings(riffdata)

        if len(db_meetings) == 0:
            # There were no meetings
            return

        self.meeting_stats['total_meetings'] = len(db_meetings)
        self.meeting_stats['first_meeting'] = min(db_meetings, key=lambda m: m['startTime'])['startTime']
        self.meeting_stats['last_meeting'] = max(db_meetings, key=lambda m: m['startTime'])['startTime']

        init_partcnt_cnt: MutableMapping[int, int] = {}  # this exists solely to define the type for reduce below
        self.meeting_stats['count_by_participants'] = reduce(inc_cnt,
                                                             [len(meeting['participants'])
                                                              for meeting in db_meetings],
                                                             init_partcnt_cnt)

        # filter the db_meetings list to exclude meetings w/ only 1 participant
        db_meetings = [meeting for meeting in db_meetings if len(meeting['participants']) > 1]

        if len(db_meetings) == 0:
            # There were no meetings with more than 1 participant
            return

        self.meeting_stats['real_meetings'] = len(db_meetings)

        self.meetings = [{'_id':              meeting['_id'],
                          'room_name':        meeting['room'],
                          'title':            meeting['title'],
                          'context':          meeting.get('context', 'No Context'),
                          'meeting_start_ts': meeting['startTime'],
                          'meeting_length':   meeting['meetingLengthMin'],
                          'participants':     meeting['participants'].copy(),
                         } for meeting in db_meetings]

        self.meetings_by_room = MeetingsData.get_meetings_by_room(self.meetings)
        self.rooms = self._get_all_room_summaries()

        meeting_durations = [meeting['meeting_length'] for meeting in self.meetings]
        self.meeting_stats['count_by_meeting_length'] = \
            MeetingsData.get_count_by_meeting_length(meeting_durations)
        self.meeting_stats['avg_meeting_length'] = sum(meeting_durations) / len(meeting_durations)
        self.meeting_stats['num_reused_rooms'] = reduce(lambda total, cnt: total + 1 if cnt > 1 else total,
                                                        [r['num_meetings'] for r in self.rooms], 0)

        # find the set of unique participants in these meetings
        all_meeting_participants: Set[str] = set().union(*[meeting['participants']
                                                           for meeting in self.meetings])
        self.meeting_stats['total_num_participants'] = len(all_meeting_participants)

        longest_meeting = max(self.meetings, key=lambda m: m['meeting_length'])
        self.meeting_stats['longest_meeting'] = {'_id':              longest_meeting['_id'],
                                                 'room':             longest_meeting['room_name'],
                                                 'title':            longest_meeting['title'],
                                                 'context':          longest_meeting['context'],
                                                 'start':            longest_meeting['meeting_start_ts'],
                                                 'length':           longest_meeting['meeting_length'],
                                                 'num_participants': len(longest_meeting['participants']),
                                                }

    def _get_db_meetings(self, riffdata):
        """
        Get the meetings in the request period from the RiffData
        """
        # constraints for the query to implement the date range
        startTimeConstraints = {}
        if self.request_period['start'] is not None:
            startTimeConstraints['$gte'] = self.request_period['start']
        if self.request_period['end'] is not None:
            startTimeConstraints['$lt'] = self.request_period['end']

        qry = {}
        qry['endTime'] = {'$ne': None}  # skip meetings w/o an endTime ( s/b only active meetings)
        if len(startTimeConstraints) > 0:
            qry['startTime'] = startTimeConstraints

        return riffdata.get_meetings(qry)

    def _get_all_room_summaries(self) -> Sequence[MutableMapping[str, Any]]:
        """
        organize, summarize and return the rooms used by self.meetings_by_room
        sorted by room name
        """
        all_room_details: Sequence[MutableMapping[str, Any]] = []
        for room_name, room_meetings in self.meetings_by_room.items():
            meeting_start_times = [meeting['meeting_start_ts'] for meeting in room_meetings]
            meeting_minutes = [meeting['meeting_length'] for meeting in room_meetings]
            participant_counts = [len(meeting['participants']) for meeting in room_meetings]
            init_part_cnt: MutableMapping[str, int] = {}  # this exists solely to define the type for reduce below
            room_details = {'room_name':        room_name,
                            'num_meetings':     len(room_meetings),
                            'first_meeting':    min(meeting_start_times),
                            'last_meeting':     max(meeting_start_times),
                            'num_participants': (min(participant_counts), max(participant_counts)),
                            'meeting_length':   (min(meeting_minutes), max(meeting_minutes)),
                            'avg_length':       sum(meeting_minutes) / len(meeting_minutes),
                            'participants':     reduce(inc_cnt,
                                                       [p for meeting in room_meetings
                                                        for p in meeting['participants']],
                                                       init_part_cnt),
                           }
            all_room_details.append(room_details)

        # order the room details by room name
        all_room_details.sort(key=lambda r: r['room_name'])

        return all_room_details

    @staticmethod
    def get_count_by_meeting_length(meeting_durations) -> Sequence[Sequence[int]]:
        """
        Count the meeting durations that fall into buckets of predefined lengths
        and return the list of those counts
        """
        meeting_duration_distribution = [
            [5, 0],
            [10, 0],
            [20, 0],
            [40, 0],
            [60, 0],
            [120, 0],
            [180, 0],
            [720, 0],  # No meetings are expected to fall outside of this 12 hour bucket
        ]

        reduce(inc_bucket, meeting_durations, meeting_duration_distribution)
        return meeting_duration_distribution

    @staticmethod
    def get_meetings_by_room(meetings: Sequence[Mapping[str, Any]]
                            ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        """
        get a mapping of room name to list of meetings which used that room for all the
        given meetings
        """
        # reorganize the meetings by room
        # dict of room name to room dict containing summary values and list of meetings
        meetings_by_room: MutableMapping[str, MutableMapping[str, Any]] = {}
        for meeting in meetings:
            room_name = meeting['room_name']
            if room_name in meetings_by_room:
                meetings_by_room[room_name].append(meeting)
            else:
                meetings_by_room[room_name] = [meeting]

        return meetings_by_room


def write_room_details(meeting_data: MeetingsData,
                       detail_level: RoomDetailLevel = RoomDetailLevel.COUNT,
                       *,
                       f=sys.stdout) -> None:
    """
    Write the room details requested for the rooms in the given meeting data

    Level:

    - NONE: no room details are printed
    - COUNT: every room name is listed with the number of times that room was used for a meeting
    - SUMMARY: every room name is listed with a summary of the usage of that room including
        - number of times the room was used
        - shortest and longest meeting times in the room
        - fewest and most participants in the room
    - SUMMARY_ATTENDEES: SUMMARY information and a list of all participants with a count of the
      number of meetings in the room that participant attended
    - ALL_MEETINGS: every room name is listed followed by complete details of each meeting that
      took place in the room
    """
    if detail_level is RoomDetailLevel.NONE:
        # write nothing
        return

    # all detail levels except none show how many rooms were used by the meetings
    rooms = meeting_data.rooms
    f.write(f'{len(rooms)} rooms used\n')

    if detail_level is RoomDetailLevel.COUNT:
        # write each room and a count of how many times it was used
        f.write('Count of the number of times a meeting room was used:\n')
        for room in rooms:
            f.write('{room_name}: {num_meetings}\n'.format(**room))
        return

    if detail_level is RoomDetailLevel.ALL_MEETINGS:
        def write_meeting(f, m):
            end = m['meeting_start_ts'] + timedelta(minutes=m['meeting_length'])
            f.write('meeting "{title}" ({_id}) in room {room_name} ({meeting_length:.1f} minutes)\n'
                    '{meeting_start_ts:%Y %b %d %H:%M} — {end:%H:%M}\n'
                    '{num_participants} participants:\n'
                    .format(**m, end=end, num_participants=len(m['participants'])))

            i = 0
            for p_id in m['participants']:
                i += 1
                f.write(f'  {i:2}) {p_id}\n')

        # write each room and a count of how many times it was used
        # along w/ the details of all meetings in that room
        for room in rooms:
            f.write('{room_name}: {num_meetings}\n'.format(**room))
            for meeting in meeting_data.meetings_by_room[room['room_name']]:
                write_meeting(f, meeting)
                f.write('\n')
        return

    if detail_level is RoomDetailLevel.SUMMARY or detail_level is RoomDetailLevel.SUMMARY_ATTENDEES:
        # print summary information about the meetings in each room
        for room in rooms:
            # shorter var names for summary info (I think we can do even better)
            shortest_meeting = room['meeting_length'][0]
            longest_meeting = room['meeting_length'][1]
            avg_meeting = room['avg_length']
            fewest_participants = room['num_participants'][0]
            most_participants = room['num_participants'][1]

            f.write('{room_name}: {num_meetings} meetings\n'.format(**room))

            if fewest_participants == most_participants:
                f.write(f'\tattended by {fewest_participants} participants\n')
            else:
                f.write(f'\tattended by {fewest_participants} - {most_participants} participants\n')

            if shortest_meeting == longest_meeting:
                f.write(f'\tlasting {shortest_meeting:.1f} minutes\n')
            else:
                f.write(f'\tlasting from {shortest_meeting:.1f} to {longest_meeting:.1f} minutes'
                        f' (avg: {avg_meeting:.1f})\n')

            if detail_level is RoomDetailLevel.SUMMARY_ATTENDEES:
                f.write('\troom participants (# of meetings)\n')
                for p_id, cnt in room['participants'].items():
                    f.write(f'\t\t{p_id} ({cnt})\n')

            f.write('\n')


def write_yaml_meeting_report(meeting_data: MeetingsData, *, f=sys.stdout) -> None:
    """
    Write the meeting report to a yaml document
    """
    # In order to control the exact yaml layout for maximum readability
    # just write the lines as desired instead of using a yaml processor

    # Preamble
    f.write('%YAML 1.2\n---\n')

    # Site that generated the meeting data
    f.write('{}: {}\n'.format('site', meeting_data.site))
    f.write('\n')

    # meeting data request period
    start = meeting_data.request_period['start']
    end = meeting_data.request_period['end']
    start_value = f'{start:%Y-%m-%dT%H:%M:%SZ}' if start is not None \
                  else '# from the beginning of time'
    end_value = f'{end:%Y-%m-%dT%H:%M:%SZ}' if end is not None \
                else '# to the end of time'
    f.write('request_period:\n')
    f.write('  {:<6}: {}\n'.format('start', start_value))
    f.write('  {:<6}: {}\n'.format('end', end_value))
    f.write('\n')

    # meeting stats
    meeting_stats = meeting_data.meeting_stats
    f.write('meeting_stats:\n')

    # NO Meetings! - write truncated report!
    if meeting_stats['total_meetings'] == 0:
        f.write('  {:<23}: {}\n'.format('total_meetings', meeting_stats['total_meetings']))
        f.write('  {:<23}: {}\n'.format('real_meetings', meeting_stats['real_meetings']))
        f.write('  {:<23}: {:.1f}\n'.format('avg_meeting_length', meeting_stats['avg_meeting_length']))
        f.write('  {:<23}: {}\n'.format('total_num_participants', meeting_stats['total_num_participants']))
        f.write('...\n')
        return

    f.write('  {:<23}: {:%Y-%m-%dT%H:%M:%SZ}\n'.format('first_meeting', meeting_stats['first_meeting']))
    f.write('  {:<23}: {:%Y-%m-%dT%H:%M:%SZ}\n'.format('last_meeting', meeting_stats['last_meeting']))
    f.write('  {:<23}: {}\n'.format('total_meetings', meeting_stats['total_meetings']))
    f.write('  {:<23}: {}\n'.format('real_meetings', meeting_stats['real_meetings']))
    f.write('  {:<23}: {:.1f}\n'.format('avg_meeting_length', meeting_stats['avg_meeting_length']))
    f.write('  {:<23}: {}\n'.format('total_num_participants', meeting_stats['total_num_participants']))
    f.write('  {:<23}: {}\n'.format('num_reused_rooms', meeting_stats['num_reused_rooms']))

    longest_meeting = meeting_stats['longest_meeting']
    f.write('  longest_meeting:\n')
    f.write('    {:<19}: {}\n'.format('room', longest_meeting['room']))
    f.write('    {:<19}: {}\n'.format('title', longest_meeting['title']))
    f.write('    {:<19}: {:%Y-%m-%dT%H:%M:%SZ}\n'.format('start', longest_meeting['start']))
    f.write('    {:<19}: {:.1f}\n'.format('length', longest_meeting['length']))
    f.write('    {:<19}: {}\n'.format('num_participants', longest_meeting['num_participants']))

    count_by_participants = meeting_stats['count_by_participants']
    f.write('  count_by_participants:\n')
    for num_participants in sorted(count_by_participants):
        f.write('    - [{}, {:3d}]\n'.format(num_participants, count_by_participants[num_participants]))

    f.write('  count_by_meeting_length:  # bucket max length in minutes, count of meetings in bucket\n')
    for bucket_minutes, cnt in meeting_stats['count_by_meeting_length']:
        f.write('    - [{:3d}, {:3d}]\n'.format(bucket_minutes, cnt))

    f.write('\n')

    # rooms
    f.write(f'rooms: # {len(meeting_data.rooms)} rooms used\n')
    for room in meeting_data.rooms:
        f.write('  - {:<17}: {}\n'.format('room_name', room['room_name']))
        f.write('    {:<17}: {}\n'.format('num_meetings', room['num_meetings']))
        f.write('    {:<17}: {:%Y-%m-%dT%H:%M:%SZ}\n'
                .format('first_meeting', room['first_meeting']))
        f.write('    {:<17}: {:%Y-%m-%dT%H:%M:%SZ}\n'
                .format('last_meeting', room['last_meeting']))
        f.write('    {:<17}: [{}, {}]\n'
                .format('num_participants', room['num_participants'][0], room['num_participants'][1]))
        f.write('    {:<17}: [{:.1f}, {:.1f}]\n'
                .format('meeting_length', room['meeting_length'][0], room['meeting_length'][1]))
        f.write('    {:<17}: {:.1f}\n'.format('avg_length', room['avg_length']))

        f.write('    participants:  # participant id, num meetings attended\n')
        for p_id, cnt in room['participants'].items():
            f.write('      - ["{}", {:2d}]\n'.format(p_id, cnt))

    f.write('\n')

    # meetings
    f.write('meetings:  # does not include meetings w/ only 1 participant\n')
    for meeting in meeting_data.meetings:
        f.write('  - {:<17}: {}\n'.format('_id', meeting['_id']))
        f.write('    {:<17}: {}\n'.format('room_name', meeting['room_name']))
        f.write('    {:<17}: {}\n'.format('meeting_title', meeting['title']))
        f.write('    {:<17}: {}\n'.format('meeting_context', meeting['context']))
        f.write('    {:<17}: {:%Y-%m-%dT%H:%M:%SZ}\n'.format('meeting_start_ts', meeting['meeting_start_ts']))
        f.write('    {:<17}: {}\n'.format('meeting_length', meeting['meeting_length']))

        f.write('    participants:\n')
        for p_id in meeting['participants']:
            f.write('      - {}\n'.format(p_id))

    # yaml document end marker
    f.write('...\n')


def write_human_meeting_report(meeting_data: MeetingsData,
                               detail_level: RoomDetailLevel,
                               *,
                               f=sys.stdout) -> None:
    """
    Write the meeting report to a human readable document
    """
    meeting_stats = meeting_data.meeting_stats
    if meeting_stats['total_meetings'] == 0:
        f.write('There were no meetings found\n')
        return

    request_period = meeting_data.request_period
    f.write('There were {meetings} meetings{req_from}{req_to}\n'
            '  first meeting on: {first:%b %d %Y}\n'
            '  last meeting on:  {last:%b %d %Y}\n\n'
            .format(meetings=meeting_stats['total_meetings'],
                    req_from='' if request_period['start'] is None
                             else f' from {request_period["start"]:%b %d %Y}',
                    req_to='' if request_period['end'] is None
                           else f' through {request_period["end"]:%b %d %Y}',
                    first=meeting_stats['first_meeting'],
                    last=meeting_stats['last_meeting']))

    count_by_participants = meeting_stats['count_by_participants']
    f.write('Number of meetings grouped by number of participants:\n')
    for num_participants in sorted(count_by_participants):
        f.write('  {:2d}: {:3d}\n'.format(num_participants, count_by_participants[num_participants]))

    f.write('\n')

    if meeting_stats['real_meetings'] == 0:
        f.write('There were no meetings with more than 1 participant\n')
        return

    f.write(f'Number of meetings with more than 1 participant was {meeting_stats["real_meetings"]}\n')

    count_by_meeting_length = meeting_stats['count_by_meeting_length']
    f.write(f'The {meeting_stats["real_meetings"]} meetings grouped by meeting length in minutes:\n')
    write_buckets(count_by_meeting_length, f=f)
    f.write('\n')

    longest_meeting = meeting_stats['longest_meeting']
    f.write('The longest meeting was:\n'
            'meeting "{title}" ({_id}) in room {room} ({length:.1f} minutes)\n'
            '{start:%Y %b %d %H:%M} — {end:%H:%M} with '
            '{num_participants} participants\n\n'
            .format(**longest_meeting,
                    end=longest_meeting['start'] + timedelta(minutes=longest_meeting['length'])))

    f.write(f'Average length of a meeting was {meeting_stats["avg_meeting_length"]:.1f} minutes\n\n')

    f.write('Total number of participants in these meetings was '
            f'{meeting_stats["total_num_participants"]}\n\n')

    # write the requested room details
    write_room_details(meeting_data, detail_level, f=f)


def do_analysis(meeting_date_range=(None, None),
                room_detail: str = 'count',
                *,
                report_format: str = 'human') -> None:
    """
    Analyze the meetings in the requested date range and write a report
    """
    riffdata = Riffdata()
    meeting_data = MeetingsData(riffdata, meeting_date_range)

    if report_format == 'human':
        write_human_meeting_report(meeting_data, RoomDetailLevel(room_detail))
    elif report_format == 'yaml':
        write_yaml_meeting_report(meeting_data)


if __name__ == '__main__':
    do_analysis()
