#################################################################################
# main.py                                                                       #
#################################################################################
#
# This is the main module to provide context for all the local application pkgs
#
# Created on    December 2, 2019
# author        Michael Jay Lippert
#
# (c) 2019-present Riff Learning Inc.,
# MIT License (see https://opensource.org/licenses/MIT)
#
#################################################################################

# Standard library imports
from datetime import timedelta

# Third party imports
import matplotlib.pyplot as plt
import numpy as np

# Local application imports
from visualize.utterance_duration import do_analysis

def _test():
    do_analysis()


if __name__ == '__main__':
    _test()
