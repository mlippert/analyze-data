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
from datetime import datetime
from functools import reduce

# Local application imports
from riffdata.riffdata import Riffdata


def inc_cnt(d, key):
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


def print_buckets(buckets):
    prev_b = None
    for b in buckets:
        if prev_b is None:
            print(f'  {"":4} < {b[0]:4}: {b[1]:4}')
        else:
            print(f'  {prev_b[0]:4} - {b[0]:4}: {b[1]:4}')
        prev_b = b


def do_analysis():
    riffdata = Riffdata()
    meeting_date_range = (datetime(2019, 9, 11), datetime(2019, 12, 4))
    qry = {'startTime': {'$gte': meeting_date_range[0],
                         '$lt': meeting_date_range[1],
                        }
          }
    meetings = riffdata.get_meetings(qry)
    print(f'There were {len(meetings)} meetings from {meeting_date_range[0]:%b %d %Y} through {meeting_date_range[1]:%b %d %Y}\n')

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

    # find the set of unique participants in these meeting
    all_meeting_participants = set().union(*[meeting['participants'] for meeting in meetings])
    print(f'Total number of participants in these meetings was {len(all_meeting_participants)}\n')


if __name__ == '__main__':
    do_analysis()
