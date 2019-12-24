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

# Local application imports
from visualize.utterance_duration import do_analysis as do_utterance_duration_analysis
from visualize.zero_duration_distrib import do_analysis as do_zero_duration_analysis
from visualize.utterance_gap_len import do_analysis as do_utterance_gap_analysis
from visualize.meetings import do_analysis as do_meetings_analysis


def _test():
    # do_meetings_analysis()
    # do_utterance_duration_analysis()
    do_utterance_gap_analysis()
    # do_zero_duration_analysis()


if __name__ == '__main__':
    _test()
