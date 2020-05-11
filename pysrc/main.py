#!/usr/bin/env python
"""
################################################################################
  main.py
################################################################################

This is the main module to provide context for all the local application pkgs

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

# Third party imports
import click

# Local application imports
from visualize.utterance_duration import do_analysis as do_utterance_duration_analysis
from visualize.zero_duration_distrib import do_analysis as do_zero_duration_analysis
from visualize.utterance_gap_len import do_analysis as do_utterance_gap_analysis
from visualize.meetings import do_analysis as do_meetings_analysis
from visualize.meeting_timeline import do_analysis as do_meeting_timeline_analysis
from riffdata.riffdata import do_drop_db as do_drop_riffdata_db, do_extract_participant


@click.command()
def utterance_gaps():
    """
    Produce a histogram plot of the gap between a participant's utterances in a meeting
    Using the gaps from all participants in all meetings.
    see plot_gap.png
    """
    do_utterance_gap_analysis()


@click.command()
def utterance_duration():
    """
    Produce a "histogram" plot of the duration of all utterances of length > 0.
    see plot.png
    """
    do_utterance_duration_analysis()


@click.command()
def zero_len_utterance_distribution():
    """
    Produce a "histogram" plot of distribution of the zero length utterances.

    The goal is to see if they may have meaning or if they are being produced by error.
    see plot_0_distrib.png
    """
    do_zero_duration_analysis()


@click.command()
def drop_riffdata_db():
    """
    Drop the riffdata database, so that a backup can be restored cleanly.
    """
    do_drop_riffdata_db()


@click.command()
@click.option('--from', '-s', 'start_date', type=click.DateTime(('%Y-%m-%d',)), default=None, required=False, help='Date of the earliest meetings to include, defaults to include earliest meeting')
@click.option('--to', '-e', 'end_date', type=click.DateTime(('%Y-%m-%d',)), default=None, required=False, help='Date following the last meetings to include, defaults to include last meeting')
@click.option('--room-detail', '-R', type=click.Choice(['none', 'count', 'summary', 'summary-attendees', 'all-meetings']), default='none', required=False, help='Room usage detail level for the selected meetings')
def meetings(start_date, end_date, room_detail):
    """
    Display information about all the meetings in a given time period.

    room details
    none - no information about the rooms used for the selected meetings
    count - every room listed with a count of the number of times it was used
    summary - every room listed with the count, min # participants, max # participants, avg length of meetings in the room
    all-meetings - every meeting in the room listed w/ its meeting info
    """
    do_meetings_analysis((start_date, end_date), room_detail)


@click.command()
@click.option('--meeting-id', '-m', type=str, default=None, required=False, help='Id of the meeting to chart')
def meeting_timeline(meeting_id):
    """
    Produce a timeline chart of the utterances by all participants in a meeting
    """
    do_meeting_timeline_analysis()


@click.command()
@click.option('--participant-id', '-p', type=str, default=None, required=True, help='Id of the participant to extract')
def extract_participant(participant_id):
    """
    Copy all data for the specified participant to the new database named 'riff_one_part'.
    That database should not exist when this is executed.

    \b
      - Their participant record
      - All data for all meetings they attended (perhaps remove lonely meetings)
        - All of those meeting documents
        - All participantevents documents for those meetings (perhaps remove null participant ids)
        - All utterances documents for those meetings (perhaps remove zero len utterances)
        - All participant documents of attendees of those meetings
          - remove any meetings not copied

    sample participant id's from staging.riffplatform.com (snapshot 2019-12-27-13:08:05)

    \b
       name (meeting count) : participant id

    \b
      - Amy D         (447) : jMZgnpJrX1QwAN0oUkYNme9kD4b2
      - Beth          (280) : GcOHEObyGzTShEOpSzma6VpzT2Q2
      - Mike          (253:127 w/ > 2 people) : V4Kc1uN0pgP7oVhaDjcmp6swV2F3
      - John Doucette (148) : FJwf8UtoqvRJ4jnAaqzV5hcfxAG3
      - Brec Hanson   (122) : i6T3a2s5WpPo1dxZaRmIJlkFn4m1
      - Jordan        (107) : SDzkCh0CetQsNw2gUZS5HPX2FCe2
    """
    do_extract_participant(participant_id, 'riff_one_part')


@click.group()
def cli():
    """Run the various riffdata analyses

    Connects to the mongodb at localhost:27017
    """
    # pylint: disable=unnecessary-pass
    pass


cli.add_command(utterance_gaps)
cli.add_command(utterance_duration)
cli.add_command(zero_len_utterance_distribution)
cli.add_command(meetings)
cli.add_command(meeting_timeline)
cli.add_command(extract_participant)
cli.add_command(drop_riffdata_db)


if __name__ == '__main__':
    cli()
