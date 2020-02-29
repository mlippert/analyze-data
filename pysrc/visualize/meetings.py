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
Copyright       (c) 2019-present Riff Learning Inc.,
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
import pprint
from functools import reduce
from typing import MutableMapping, Sequence, Iterable, Union, Any
from enum import Enum

# Local application imports
from riffdata.riffdata import Riffdata


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


def inc_cnt(d: MutableMapping[Any, int], key) -> MutableMapping[Any, int]:
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


def inc_bucket(buckets, v):
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


def print_buckets(buckets: Iterable[Sequence[Any]]):
    prev_b = None  # type: Union[Sequence[Any], None]
    for b in buckets:
        if prev_b is None:
            print(f'  {"":4} < {b[0]:4}: {b[1]:4}')
        else:
            print(f'  {prev_b[0]:4} - {b[0]:4}: {b[1]:4}')
        prev_b = b


def print_room_details(meetings, detail_level: RoomDetailLevel = RoomDetailLevel.COUNT) -> None:
    """
    Print the room details for the rooms used by the given meetings

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
        # print nothing
        return

    # reorganize the meetings by room
    rooms = {}      # dict of room name to list of meetings in that room
    for meeting in meetings:
        room_name = meeting['room']
        if room_name in rooms:
            rooms[room_name].append(meeting)
        else:
            rooms[room_name] = [meeting]

    # all detail levels except none show how many rooms were used by the meetings
    print(f'{len(rooms)} rooms used')

    if detail_level is RoomDetailLevel.COUNT:
        # print each room and a count of how many times it was used
        print('Count of the number of times a meeting room was used:')
        for room_name, room_meetings in rooms.items():
            print(f'{room_name}: {len(room_meetings)}')
        return

    if detail_level is RoomDetailLevel.SUMMARY:
        # print summary information about the meetings in each room
        for room_name, room_meetings in rooms.items():
            meeting_minutes = [meeting['meetingLengthMin'] for meeting in room_meetings]
            shortest_meeting = min(meeting_minutes)
            longest_meeting = max(meeting_minutes)
            avg_meeting = sum(meeting_minutes) / len(meeting_minutes)

            participant_counts = [len(meeting['participants']) for meeting in room_meetings]
            fewest_participants = min(participant_counts)
            most_participants = max(participant_counts)

            room_participants = reduce(inc_cnt, [p for meeting in room_meetings for p in meeting['participants']], {})

            print(f'{room_name}: {len(room_meetings)} meetings')
            if fewest_participants == most_participants:
                print(f'\tattended by {fewest_participants} participants')
            else:
                print(f'\tattended by {fewest_participants} - {most_participants} participants')
            if shortest_meeting == longest_meeting:
                print(f'\tlasting {shortest_meeting:.1f} minutes')
            else:
                print(f'\tlasting from {shortest_meeting:.1f} to {longest_meeting:.1f} minutes (avg: {avg_meeting:.1f})')
            print()
        return

    if detail_level is RoomDetailLevel.SUMMARY_ATTENDEES:
        # print each room and a count of how many times it was used
        print('SUMMARY_ATTENDEES room detail is not implemented')
        # TODO: most of the summary info is the same as for SUMMARY, so we need to figure out how
        # to not duplicate the calculations and output. The unused room_participants in SUMMARY is
        # actually for use here!
        return

    if detail_level is RoomDetailLevel.ALL_MEETINGS:
        # print each room and a count of how many times it was used
        for room_name, room_meetings in rooms.items():
            print(f'{room_name}: {len(room_meetings)}')
            for meeting in room_meetings:
                Riffdata.print_meeting(meeting)
                print()
        return


def do_analysis(meeting_date_range=(None, None), room_detail: str = 'count'):
    riffdata = Riffdata()

    # display strings for the start and end of the date range
    from_constraint = ''
    to_constraint = ''
    # constraints for the query to implement the date range
    startTimeConstraints = {}
    if meeting_date_range[0] is not None:
        startTimeConstraints['$gte'] = meeting_date_range[0]
        from_constraint = f'from {meeting_date_range[0]:%b %d %Y}'
    if meeting_date_range[1] is not None:
        startTimeConstraints['$lt'] = meeting_date_range[1]
        to_constraint = f'through {meeting_date_range[1]:%b %d %Y}'

    qry = None
    if len(startTimeConstraints) > 0:
        qry = {'startTime': startTimeConstraints}

    meetings = riffdata.get_meetings(qry)

    if len(meetings) == 0:
        print('There were no meetings found')
        return

    first_meeting_start = min(meetings, key=lambda m: m['startTime'])['startTime']
    last_meeting_start = max(meetings, key=lambda m: m['startTime'])['startTime']
    print(f'There were {len(meetings)} meetings {from_constraint} {to_constraint}\n'
          f'  first meeting on: {first_meeting_start:%b %d %Y}\n'
          f'  last meeting on:  {last_meeting_start:%b %d %Y}\n')

    meetings_w_num_participants = reduce(inc_cnt, [len(meeting['participants']) for meeting in meetings], {})
    print('Number of meetings grouped by number of participants:')
    pprint.pprint(meetings_w_num_participants)
    print()

    meetings = [meeting for meeting in meetings if len(meeting['participants']) > 1]
    print(f'Number of meetings with more than 1 participant was {len(meetings)}')

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

    meeting_durations = [meeting['meetingLengthMin'] for meeting in meetings]
    reduce(inc_bucket, meeting_durations, meeting_duration_distribution)
    print(f'The {len(meetings)} meetings grouped by meeting length in minutes:')
    # pprint.pprint(meeting_duration_distribution)
    print_buckets(meeting_duration_distribution)
    print()

    longest_meeting = max(meetings, key=lambda m: m['meetingLengthMin'])
    print('The longest meeting was:')
    Riffdata.print_meeting(longest_meeting)
    print()

    avg_meeting_duration = sum(meeting_durations) / len(meeting_durations)
    print(f'Average length of a meeting was {avg_meeting_duration:.1f} minutes\n')

    # find the set of unique participants in these meetings
    all_meeting_participants = set().union(*[meeting['participants'] for meeting in meetings])
    print(f'Total number of participants in these meetings was {len(all_meeting_participants)}\n')

    # print the requested room details
    print_room_details(meetings, RoomDetailLevel(room_detail))


if __name__ == '__main__':
    do_analysis()
