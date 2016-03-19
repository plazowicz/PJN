__author__ = 'mateuszopala'
from nltk.metrics.distance import edit_distance


czech_bug_punishment = 0.2
spelling_error_punishment = 0.2
diacritical_error_punishment = 0.2


def levensthein_dist(s1, s2):
    return edit_distance(s1, s2, transpositions=False)


def levensthein_punishing_spelling_errors(s1, s2):
    base_dist = levensthein_dist(s1, s2)


class WordCorrector(object):
    pass
