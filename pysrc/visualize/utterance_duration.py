"""
################################################################################
  visualize.utterance_duration.py
################################################################################

This module produces visualizations of riffdata utterance duration

=============== ================================================================
Created on      December 2, 2019
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2019-present Riff Learning Inc.,
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
from datetime import timedelta

# Third party imports
import matplotlib.pyplot as plt
import numpy as np

# Local application imports
from riffdata.riffdata import Riffdata


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


def _make_xy_sets_to_plot(x_src, y_src, ranges):
    """
    convert the x_src and y_src into lists of np.arrays so that
    each range given can be plotted.
    e.g. if ranges=[1, 10, 100, 1000]
        x[0] and y[0] will contain [1:10]
        x[1] and y[1] will contain [10:100]
        x[2] and y[2] will contain [100:1000]
        from the respective x_src and y_src
    """
    # must have at least 2 indices in ranges, not checking for that yet
    x = []
    y = []
    start = ranges[0]
    for end in ranges[1:]:
        x.append(np.array(x_src[start:end]))
        y.append(np.array(y_src[start:end]))
        start = end

    return x, y


def _print_participant_uts_info(meeting_id, participant_uts):
    print(f'For the meeting with id {meeting_id}:')
    for participant_id in participant_uts:
        print(f'  participant id {participant_id} had {len(participant_uts[participant_id])} utterances')


def _print_bucket_data(buckets, bucket_cnt):
    for i in range(0, len(bucket_cnt) - 1):
        print(f'{timedelta(milliseconds=buckets[i])}: {bucket_cnt[i]}')

    print(f'>: {bucket_cnt[len(bucket_cnt) - 1]}')


def _distribute_durations(durations):
    """
    :param durations: sorted list of utterance durations in ms
    :type durations: list
    :return: A tuple consisting of the a list of buckets in ms, a matching list
             of the count of utterances in that bucket w/ a final element w/ the
             count of remaining unbucketed utterances, and a graph range list
             for partitioning the buckets into visually relevant plots
    """
    buckets = [0, 2, 5,                         # .   0 -   2
               *range(10, 300, 10),             # .   3 -  32
               *range(300, 3500, 50),           # .  33 -  96
               *range(3500, 8001, 500),         # .  97 - 106
               *range(10000, 60001, 10000),     # . 107 - 113
              ]

    graph_ranges = [1, 33, 97, 107]

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

    return buckets, bucket_cnt, graph_ranges


def do_analysis():
    riffdata = Riffdata()
    meetings = riffdata.get_meetings_with_participant_utterances()

    print(f'Found utterances from {len(meetings)} meetings')
    meeting_ids = list(meetings)

    # Just to get an idea of what is in a meeting w/ participant utterances print 1
    _print_participant_uts_info(meeting_ids[0], meetings[meeting_ids[0]])

    durations = get_utterance_durations(meetings)
    print(f'Found {len(durations)} utterances')

    durations.sort()
    print(f'shortest utterance was {durations[0]}ms and longest was {durations[-1]}ms')

    buckets, bucket_cnt, graph_ranges = _distribute_durations(durations)
    _print_bucket_data(buckets, bucket_cnt)

    x, y = _make_xy_sets_to_plot(x_src=buckets, y_src=bucket_cnt, ranges=graph_ranges)

    # pylint: disable=consider-using-enumerate
    fig, ax = plt.subplots(len(x), 1)
    for plot in range(0, len(x)):
        my_plotter(ax[plot], x[plot], y[plot], {'marker': 'x'})

    fig.savefig('plot.png')


if __name__ == '__main__':
    do_analysis()
