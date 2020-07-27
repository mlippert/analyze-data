"""
################################################################################
  riffmetrics.utils.py
################################################################################

The riffmetrics.utils module contains utilities for manipulating the riff data

=============== ================================================================
Created on      June 11, 2020
--------------- ----------------------------------------------------------------
author(s)       Michael Jay Lippert
--------------- ----------------------------------------------------------------
Copyright       (c) 2020-present Michael Jay Lippert
                MIT License (see https://opensource.org/licenses/MIT)
=============== ================================================================
"""

# Standard library imports
import logging
import pprint
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


def merge_utterances(uts: list, min_gap: int):
    """
    Create a new list of utterances by copying the given list and merging
    utterances which are "closer" than the specified minimum gap (in
    milliseconds). An utterance which is too close to the previous one is
    merged by changing the end time of the previous utterance to the end time
    of the current one and removing the current utterance.

    uts will be sorted ascending by the 'start' key value.
    No utterances in uts will be modified.

    :param uts: A list of utterances where an utterance is a dict with at least the
                following keys:
                - 'start': a type which end can be subtracted from resulting in the number of ms
                - 'end': a type which can be subtracted from start resulting in the number of ms
    :type uts: list

    :param min_gap: The minimum gap between the end of one utterance and the start
                    of the next in the returned list of utterances.
    :type min_gap: int

    :return: A list of merged utterances
    :rtype: list
    """
    uts.sort(key=lambda ut: ut['start'])
    processed_uts = []
    cur_ut = uts[0].copy()
    for ut in uts[1:]:
        if ut['start'] - cur_ut['end'] < min_gap:
            cur_ut['end'] = ut['end']
        else:
            processed_uts.append(cur_ut)
            cur_ut = ut.copy()
    processed_uts.append(cur_ut)

    return processed_uts


def compute_pairwise_relations(ordered_items: Sequence[T],
                               is_related: Callable[[T, T], bool],
                               is_possibly_related: Optional[Callable[[T, T], bool]] = None)
                               -> MutableSequence[Tuple[T, T]]:
    """
    Get the list of related items as determined by the isRelated predicate
    function.  Every item in the given orderedItems list will be "compared"
    to every other item in that list.

    The is_related predicate that determines if there is a relationship between
    2 items is always called with 2 items from the item list with the 1st
    item argument being before the 2nd item argument in the item list.

    As an optimization, the is_possibly_related function may be supplied to
    determine if an earlier item in the list can be related to any items
    later than the first of the remaining items to be tested, and if that
    function returns false, that earlier item will not be compared to that
    first item or any of the later items.

    DevNote:
     The algorithm used is:
       split the ordered items in 2, items from the front of the list
       to be compared against all the remaining items in the list,
       and the remaining items in the list.
       Then:
       - Optimize by using the isPossiblyRelated function to remove items
         from the first list before comparing against the 1st item in the
         2nd list.
       - Compare all the items in the first list against the 1st item in
         the 2nd list.
       - Move the 1st item in the 2nd list to the 1st list.
       - Repeat until there are no more items in the 2nd list.

    :param ordered_items: the items to be compared (order is only important
                          to the order of arguments to the predicates supplied)
    :type ordered_items: Sequence[T]

    :param is_related: function that returns true if the 2 given items are related
                       item2 will always be from after item1 in the ordered_items list.
    :type is_related: Callable[[T, T], bool]

    :param is_possibly_related: function that compares a candidate item, which
                                will be an earlier item than the first
                                remaining item, against the first remaining
                                item and returns true if the candidate item
                                cannot be related to the first remaining item
                                or ANY of the items that follow it in the
                                ordered_items list. f(later_item, earlier_item)
    :type is_possibly_related: Optional[Callable[[T, T], bool]]

    :return: A list of tuples of items that are related
    :rtype: MutableSequence[Tuple[T, T]]
    """
    # The 1st item has nothing before it to compare against so immediately move it from the
    # remaining list to the candidate list
    candidate_items = [ordered_items[0]]
    remaining_items = ordered_items[1:]

    related_items = []
    for test_item in remaining_items
        # remove candidate items that can't be related to any remaining_items so we don't bother testing them
        if is_possibly_related is not None:
            candidate_items = [item for item in candidate_items if is_possibly_related(test_item, item)]

        # compare the candidate items to the test item and create a list of tuples of related items
        new_related_items = [item, test_item for item in candidate_items if is_related(item, test_item)]

        # append new related items
        related_items.extend(new_related_items);

        # the test item becomes a candidate to test against the remaining items
        candidate_items.append(test_item);
    }

    return related_items


def count_relations(relations: Sequence[Tuple[T, T]],
                    get_item_key: Callable[[T], str]) -> Dict[str, dict]:
    """
    Count the relations when grouping the Items in the relations by a string
    property key.

    Notes:
     - relations are pairs of Items (an item can be almost anything).
     - a relation is not commutative ie the pair [item1, item2] is NOT the
       same as the pair [item2, item1].
     - It may be that the item key of item1 and item2 are the same, that is
       the responsibility of the caller and the supplied get_item_key function.

    :param relations:
    :type relations: Sequence[Tuple[T, T]]

    :param get_item_key:
    :type get_item_key: Callable[[T], str]

    :return: A map of "key1+key2" to a dict w/ key1, key2 and the count of
             the relations with those keys.
    :rtype: Dict[str, dict]
    """
    relation_counts = {}

    for relation in relations:
        key1 = get_item_key(relation[0])
        key2 = get_item_key(relation[1])
        relation_key = key1 + key2

        if relation_key in relation_counts:
            relation_counts[relation_key]['count'] += 1
        else:
            relation_counts[relation_key] = {'key1': key1,
                                             'key2': key2,
                                             'count': 1,
                                            }

    return relation_counts


def compute_utterance_pairwise_relations(sorted_utterances,
                                         participants,
                                         is_related,
                                         is_possibly_related):
    """
    """
    related_utterances = compute_pairwise_relations(sorted_utterances, is_related, is_possibly_related);
    relation_counts = count_relations(related_utterances, lambda u: u['participant']);

    return relation_counts, related_utterances


# Affirmation constants (times in milliseconds)
AFFIRMATION_MIN_OVERLAP = 250
AFFIRMATION_MAX_LENGTH = 2000

def get_meeting_affirmations(meeting: Meeting):
    """
    Goal is to create counts of who affirmed whom.
    A affirms B if A begins to speak while B is speaking;
    and A and B's speach overlaps for at least .25 seconds;
    and A speaks for less than 2 seconds before stopping;
    and B continues talking after A stops talking.
    """
    def is_possibly_related(later_ut, earlier_ut) -> bool:
        """
        If the earlier utterance ends after the later utterance starts,
        future utterances could possibly affirm the earlier utterance.
        """
        time_diff = getDurationInSeconds(earlier_ut.endTime, later_ut.startTime);
        keep = time_diff < 0

        return keep

    def is_affirmation(earlier_ut, later_ut) -> bool:
        """
        Does the later utterance affirm the earlier utterance?
        """
        if earlier_ut['participant'] == later_ut['participant']:
            return False  # can't affirm yourself

        # Do they overlap for long enough?
        sufficient_overlap = earlier_ut['end'] - later_ut['start'] > AFFIRMATION_MIN_OVERLAP:
        # Is the affirming utterance less than 2 seconds?
        short_affirmation = later_ut['end'] - later_ut['start'] < AFFIRMATION_MAX_LENGTH
        # Does the affirming utterance stop before the earlier utterance stops?
        affirmation_ends = earlier_ut['end'] - later_ut['end'] > 0

        is_affirming = sufficient_overlap && short_affirmation && affirmation_ends

        return is_affirming

    affirmations = compute_utterance_pairwise_relations(meeting.utterances,
                                                        meeting.participants,
                                                        is_affirmation,
                                                        is_possibly_related
                                                       )


def get_meeting_interruptions(meeting):
    """
 * Goal is to create counts of who interrupted whom.
 * A interrupts B if A begins to speak while B is speaking;
 * and A and B's speach overlaps for at least a second;
 * and A speaks for at least 5 seconds before stopping;
 * and B gives up and stops talking before A stops talking.
    """
    def is_possibly_related(later_ut, earlier_ut) -> bool:
        """
        If the earlier utterance ends after the later utterance starts,
        future utterances could possibly affirm the earlier utterance.
        """
        time_diff = getDurationInSeconds(earlierUtt.endTime, laterUtt.startTime);
        keep = time_diff < 0

        return keep

    def is_interruption(earlier_ut, later_ut) -> bool:
        """
        Does the later utterance interrupt the earlier utterance?
        """
        if earlier_ut['participant'] == later_ut['participant']:
            return False  # can't interrupt yourself

        # Do they overlap for long enough?
        sufficient_overlap = earlier_ut['end'] - later_ut['start'] > AFFIRMATION_MIN_OVERLAP:
        # Is the affirming utterance less than 2 seconds?
        short_affirmation = later_ut['end'] - later_ut['start'] < AFFIRMATION_MAX_LENGTH
        # Does the affirming utterance stop before the earlier utterance stops?
        affirmation_ends = earlier_ut['end'] - later_ut['end'] > 0

        is_affirming = sufficient_overlap && short_affirmation && affirmation_ends

        return is_affirming





# Convert the following from javascript to python
/* ******************************************************************************
 * computeUtterancePairwiseRelations                                       */ /**
 *
 * Get all pairs of utterances from the given ordered list of utterances
 * where a given binary relationship is true. Count the identical pairs when
 * each utterance in a pair is identified by its participant id.
 *
 * The given isRelated function will be called for every pair of utterances
 * and every pair where that function returns true will be returned and counted.
 *
 * Example: Influence is a binary relation. Two utterances form an influence
 *  iff the second one starts within 3 seconds of when the first one ends.
 *  This function would compute for every pair of utterances whether the influence
 *  relation holds. It would then compute for every pair of participants the number
 *  of times one participant influences another. It returns a list of these counts,
 *  with one entry in the list for every pair of participants with at least 1
 *  influence event.
 *
 * TODO: change this to return ONLY the counts array of count objects
 *      where a count object is:
 *      { participants: Pair<Participant>,  // or participant1 and participant2 ?
 *        count: number }
 *
 * @param {Array<Utterance>} sortedUtterances
 *      All utterances, sorted by startDate.
 *
 * @param {Map<string, Participant>} speakingParticipants
 *      All participants referenced by sortedUtterances
 *
 * @param {function(ut1: Utterance, ut2: Utterance): boolean} isRelated
 *      function that returns true if the 2 given utterances are related
 *      ut2 will always be from after ut1 in the sortedUtterances list.
 *
 * @param {?function(firstRemainingUt: Utterance): function(comparisonUt: Utterance): boolean} isPossiblyRelated
 *      function that returns a function that compares an utterance against the
 *      firstRemainingUt and returns true if the comparisonUt cannot be
 *      related to the firstRemainingUt or ANY of the items that follow it
 *      in the sortedUtterances list.
 *      This is an optional argument used for efficiency and may be null
 *      or undefined.
 *      - If unused, runtime is O(|sortedUtterances|^2).
 *      - If used, runtime is O(K*|sortedUtterances|), where K is the largest
 *        number of pairs of utterances that occur close enough together to be
 *        candidates for the binaryRelation
 *
 * @returns {{ finalEdges: Array, events: Array }} object containing both the
 *      counts array (finalEdges) and the relations (events).
 *      finalEdges is an array containing 0 or more "relationCount" objects.
 *      A relationCount is:
 *      { source: a participant id,
 *        sourceName: a string,
 *        target: a participant id,
 *        targetName: a string,
 *        size: a count of the number of utterance pairs made by source & target where
 *              binaryRelation was true }
 *      events is an array containing the related utterances as an eventObject.
 *      An eventObject is:
 *      { earlierUtt: { utt: Utterance,
 *                      otherUtt: Utterance,
 *                      participantName: string,
 *                      otherParticipantName: string },
 *        laterUtt:   { utt: Utterance,                     // === earlierUtt.otherUtt
 *                      otherUtt: Utterance,                // === earlierUtt.outt
 *                      participantName: string,            // === earlierUtt.otherParticipantName
 *                      otherParticipantName: string } }    // === earlierUtt.participantName
 */
function computeUtterancePairwiseRelations(sortedUtterances, participants, isRelated, isPossiblyRelated) {
    const relatedUtterances = computePairwiseRelations(sortedUtterances, isRelated, isPossiblyRelated);
    const relationCounts = countRelations(relatedUtterances, u => u.participant);

    // functions used to recreate the old (refactored) function's return value

    const getParticipantName = pId => participants.get(pId).name || 'no name found';

    // Create an event object for the relation of the testUt to the relatedUt
    const makeEvent = (relation) => {
        const earlierUt = relation[0];
        const earlierParticipantName = getParticipantName(earlierUt.participant);
        const laterUt = relation[1];
        const laterParticipantName = getParticipantName(laterUt.participant);
        return {
            earlierUtt: {
                utt: earlierUt,
                otherUtt: laterUt,
                participantName: earlierParticipantName,
                otherParticipantName: laterParticipantName,
            },
            laterUtt: {
                utt: laterUt,
                otherUtt: earlierUt,
                participantName: laterParticipantName,
                otherParticipantName: earlierParticipantName,
            },
        };
    };

    const makeEdge = (relationCount) => {
        return {
            // id: this property was in the old value, but is never used, so I don't bother recreating it -mjl
            source: relationCount.key1,
            sourceName: getParticipantName(relationCount.key1),
            target: relationCount.key2,
            targetName: getParticipantName(relationCount.key2),
            size: relationCount.count,
        };
    };

    // recreate the return value of the computePairwiseRelation function being
    // refactored. (TODO: I think we could have a better return value -mjl)

    const finalEdges = Array.from(relationCounts.values(), makeEdge);
    const events = relatedUtterances.map(makeEvent);

    logger.debug('analysis_utils.computeUtterancePairwiseRelations is returning:', { finalEdges, events });

    return { finalEdges, events };
}


async function getAffirmationsData(sortedUtterances, speakingParticipants, meetingId, uid, dispatch) {
    dispatch({
        type: ActionTypes.DASHBOARD_FETCH_MEETING_AFFIRMATIONS,
        status: 'loading',
    });


    // If the earlier utterance ends after the later utterance starts,
    // future utterances could possibly affirm the earlier utterance.
    const keepPredicate = laterUtt => (earlierUtt) => {
        const timeDiff = getDurationInSeconds(earlierUtt.endTime, laterUtt.startTime);
        const keep = timeDiff < 0;

        return keep;
    };

    // Does the later utterance affirm the earlier utterance?
    const affirmationPredicate = (earlierUtt, laterUtt) => {
        if (earlierUtt.participant === laterUtt.participant) {
            return false; // can't affirm yourself
        }

        // Do they overlap for long enough?
        const sufficientOverlap = getDurationInSeconds(laterUtt.startTime, earlierUtt.endTime) > .25;
        // Is the interruption less than 2 seconds?
        const shortAffirmation = getDurationInSeconds(laterUtt.startTime, laterUtt.endTime) < 2;
        // Does the affirmation stop before the earlier utterance stops?
        const affirmationsEnds = getDurationInSeconds(laterUtt.endTime, earlierUtt.endTime) > 0;

        const isAffirming = sufficientOverlap && shortAffirmation && affirmationsEnds;
        return isAffirming;
    };

    const affirmationsData = computeUtterancePairwiseRelations(
        sortedUtterances,
        speakingParticipants,
        affirmationPredicate,
        keepPredicate
    );

def _test():
    pass


if __name__ == '__main__':
    _test()
