"""
################################################################################
  visualize.zero_duration_distrib.py
################################################################################

This module produces a visualization of the distribution within a meeting of
zero length utterances

=============== ================================================================
Created on      December 4, 2019
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2019-present Riff Learning Inc.,
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
from datetime import timedelta
from functools import reduce
from typing import List

# Third party imports
import matplotlib.pyplot as plt
import numpy as np

# Local application imports
from riffdata.riffdata import Riffdata


def get_zerolen_ut_distribution(meetings) -> List[int]:
    """
    Distribute the utterances of a meeting into buckets representing the percentile
    of the meeting duration, summing the percentiles over all meetings.

    :param meetings: map of meeting ids to a map of participant ids to the list
                     of utterances by that participant in that meeting

    :return: list of counts of the zero length utterances in a percentile
             of the meeting duration.
    """
    num_buckets = 50
    distributions = [0 for i in range(0, num_buckets)]

    def distribute(distributions, bucket):
        distributions[bucket] += 1
        return distributions

    for meeting_id in meetings:
        participant_uts = meetings[meeting_id]
        # combine all the utterances from the meeting into a single list
        all_meeting_uts = [ut for p_id in participant_uts for ut in participant_uts[p_id]]
        if len(all_meeting_uts) == 0:
            continue

        # use the utterances to determine the meeting start and end
        meeting_start = min(all_meeting_uts, key=lambda ut: ut['start'])['start']
        meeting_end = max(all_meeting_uts, key=lambda ut: ut['end'])['end']
        meeting_duration = meeting_end - meeting_start
        if meeting_duration < timedelta(minutes=1):
            continue

        # increase the bucket_size by 1ms to avoid the issue if the last utterance is
        # a 0 length utterance. This should not have any real affect on the results.
        bucket_size = (meeting_end - meeting_start) / num_buckets + timedelta(milliseconds=1)

        # create a list of the bucket for each utterance of len 0 and then sum those into
        # the distributions list of bucket counts
        reduce(distribute, [(ut['start'] - meeting_start) // bucket_size
                            for ut in all_meeting_uts if ut['duration'] == 0],
               distributions)

    return distributions


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


def do_analysis():
    riffdata = Riffdata()
    meetings = riffdata.get_meetings_with_participant_utterances()

    print(f'Found utterances from {len(meetings)} meetings')

    zerolen_ut_distribution = get_zerolen_ut_distribution(meetings)

    percentile_size = 100 // len(zerolen_ut_distribution)
    x = np.array(range(percentile_size, 101, percentile_size))
    y = np.array(zerolen_ut_distribution)

    # pylint: disable=consider-using-enumerate
    fig, ax = plt.subplots()
    my_plotter(ax, x, y, {'marker': 'x'})

    fig.savefig('plot_0_distrib.png')


if __name__ == '__main__':
    do_analysis()
