"""
################################################################################
  riffmetrics.meeting.py
################################################################################

The riffmetrics.meeting module defines a Riff Meeting class

=============== ================================================================
Created on      July 25, 2020
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2020-present Michael Jay Lippert
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
import logging
from datetime import timedelta
from typing import (Any,
                    Callable,
                    Iterable,
                    MutableMapping,
                    MutableSequence,
                    Optional,
                    Sequence,
                    Set,
                    Tuple,
                    TypeVar,
                    Union,
                   )

# Third party imports

# Local application imports


# Generic type variable for defining function parameters
T = TypeVar('T')

# Type aliases
MeetingId = str
ParticipantId = str
ParticipantUtterances = Mapping[ParticipantId, Sequence[Utterance]]
Milliseconds = int


class Meeting:
    """
    """

    def __init__(self, *,
                 m_id: MeetingId,
                 site_id: str='',
                 meeting_name: str='',
                 room_name: str,
                 meeting_start_ts: DateTime,
                 meeting_start: Milliseconds=0,
                 meeting_end: Milliseconds=0,
                 participants: Sequence[Participant]=[],
                 events: Sequence[MeetingEvent]=[],
                 utterances: Sequence[Utterance]=[],
                ):
        """
        """
        self.logger = logging.getLogger('riffAnalytics.RiffMetrics.Meeting')

        self.meeting_id: MeetingId = meeting_id
        self.participant_uts: ParticipantUtterances = participant_uts


class Utterance:
    """
    An utterance is a period of speaking during a meeting by a participant in
    that meeting.
    It is identified by the id of the participant who spoke and the start
    and end time of the utterance. These times are kept in milliseconds from
    the beginning of the meeting, and therefore are only relevant to other
    utterances in the same meeting.
    """

    def __init__(self, *, p_id: ParticipantId, start: Milliseconds, end: Milliseconds):
        """
        """
        self.logger = logging.getLogger('riffAnalytics.RiffMetrics.Utterance')

        # id of participant who made the utterance
        self.p_id: ParticipantId = p_id

        # offset in ms from the start of the meeting the utterance was made in to the start of the utterance
        self.start: Milliseconds = start

        # offset in ms from the start of the meeting the utterance was made in to the end of the utterance
        self.end: Milliseconds = end


class Participant:
    """
    """

    def __init__(self, *, p_id: ParticipantId, name: str='anonymous'):
        """
        """
        self.logger = logging.getLogger('riffAnalytics.RiffMetrics.Participant')

        # unique id of the participant
        self.p_id: ParticipantId = p_id

        # display name of the participant (if known, otherwise 'anonymous')
        self.name: str = name

