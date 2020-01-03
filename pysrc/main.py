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
@click.option('--from', '-s', 'start_date', type=click.DateTime(('%Y-%m-%d',)), default=None, required=False, help='Date of the earliest meetings to include, defaults to include earliest meeting')
@click.option('--to', '-e', 'end_date', type=click.DateTime(('%Y-%m-%d',)), default=None, required=False, help='Date following the last meetings to include, defaults to include last meeting')
def meetings(start_date, end_date):
    """
    Display information about all the meetings in a given time period.
    """
    do_meetings_analysis((start_date, end_date))


@click.command()
@click.option('--meeting-id', '-m', type=str, default=None, required=False, help='Id of the meeting to chart')
def meeting_timeline(meeting_id):
    """
    Produce a timeline chart of the utterances by all participants in a meeting
    """
    do_meeting_timeline_analysis()


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


if __name__ == '__main__':
    cli()
