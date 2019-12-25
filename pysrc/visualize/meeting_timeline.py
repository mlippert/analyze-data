"""
################################################################################
  visualize.meeting_timeline.py
################################################################################

Produce a visualization of the utterances in a meeting

This was inspired by the `stackoverflow answer <https://stackoverflow.com/a/51506028/2184226>`_

=============== ================================================================
Created on      December 25, 2019
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2019 Michael Jay Lippert,
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
from datetime import datetime
import pprint

# Third party imports
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import PolyCollection

# Local application imports
from riffdata.riffdata import Riffdata


def get_utterances_as_polycollection(participant_uts):
    """
    """
    verts = []
    colors = []
    part_num = 0
    for participant_id in participant_uts:
        uts = participant_uts[participant_id]

        part_num += 1
        part_color = f'C{part_num}'

        # use the part_ndx as the vertical (y) center position of the polygons for
        # participant's utterances
        top = part_num + .4
        bottom = part_num - .4

        for ut in uts:
            left = mdates.date2num(ut['start'])
            right = mdates.date2num(ut['end'])
            verts.append(make_rect(top, left, bottom, right))
            colors.append(part_color)

    return verts, colors


def make_rect(t, l, b, r):
    """
    Given the 4 sides, top, left, bottom and right of a rectangle return a
    list of points that will draw that rectangle (when closed).
    """
    return [(l, b), (l, t), (r, t), (r, b)]


def print_participant_utterance_counts(participant_uts):
    for participant_id in participant_uts:
        print(f'{participant_id} had {len(participant_uts[participant_id])} utterances')


def do_analysis():
    # get a meeting
    riffdata = Riffdata()
    test_meetings = ['plg-147-l2t0dt-1', 'plg-206-uzw00g-3']
    meeting = riffdata.get_meeting(test_meetings[1])
    participant_uts = meeting['participant_uts']
    Riffdata.print_meeting(meeting)

    verts, colors = get_utterances_as_polycollection(participant_uts)
    bars = PolyCollection(verts, facecolors=colors)

    fig, ax = plt.subplots()
    ax.add_collection(bars)
    ax.autoscale()
    loc = mdates.MinuteLocator(byminute=[0, 15, 30, 45])
    ax.xaxis.set_major_locator(loc)
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(loc))

    ax.set_yticks([*range(1, len(participant_uts) + 1)])
    ax.set_yticklabels(list(participant_uts))

    fig.savefig('meeting_timeline.png')


if __name__ == '__main__':
    do_analysis()
