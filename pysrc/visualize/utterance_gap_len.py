"""
################################################################################
  visualize.utterance_gap_len.py
################################################################################

[summary of file contents]

=============== ================================================================
Created on      December 24, 2019
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2019 Michael Jay Lippert,
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
from datetime import timedelta
from typing import Sequence, Mapping, List, Any

# Third party imports
import matplotlib.pyplot as plt
import numpy as np

# Local application imports
from riffdata.riffdata import Riffdata

# Types
MeetingId = str
ParticipantId = str
Utterance = Mapping[str, Any]
Meeting = Mapping[MeetingId, Mapping[ParticipantId, Sequence[Utterance]]]


def get_utterance_gaps(meetings: Sequence[Meeting]) -> List[float]:
    """
    Compute and return a list of the gaps between participant's utterances
    in milliseconds.

    :param meetings: Meetings w/ utterances grouped by participant to analyze
    :type meetings: dict

    :return: list of the gaps in milliseconds between a participant's
             utterances in a meeting
    """
    gaps = []
    processed_meeting_cnt = 0
    speaking_participant_cnt = 0

    for meeting_id in meetings:
        participant_uts = meetings[meeting_id]

        # skip meetings with only 1 person
        if len(participant_uts) < 2:
            continue

        processed_meeting_cnt += 1

        for participant_id in participant_uts:
            uts = participant_uts[participant_id]

            # filter out uts w/ 0 duration and then sort by start
            uts = [ut for ut in uts if ut['duration'] != 0]
            uts.sort(key=lambda ut: ut['start'])

            # need at least 2 uts for there to be a gap
            if len(uts) < 2:
                continue

            speaking_participant_cnt += 1

            prev_ut = uts[0]
            for cur_ut in uts[1:]:
                gaps.append((cur_ut['start'] - prev_ut['end']) / timedelta(milliseconds=1))
                prev_ut = cur_ut

    print(f'processed {speaking_participant_cnt} participants in {processed_meeting_cnt} meetings. {len(gaps)} gaps.')
    return gaps


def do_analysis():
    riffdata = Riffdata()
    meetings = riffdata.get_meetings_with_participant_utterances()

    print(f'Found utterances from {len(meetings)} meetings')

    gaps = get_utterance_gaps(meetings)

    x = np.array(gaps)
    fig, ax = plt.subplots()
    # the histogram of the data (see example: https://matplotlib.org/gallery/statistics/histogram_features.html)
    num_bins = 50
    ax.hist(x, num_bins, range=(0, 4000))

    fig.savefig('plot_gap.png')


if __name__ == '__main__':
    do_analysis()
