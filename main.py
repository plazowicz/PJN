# coding=utf-8
import cPickle
from multiprocessing import Pool
from collections import defaultdict
from nltk.metrics import edit_distance
from Levenshtein import editops
import codecs
__author__ = 'mateuszopala'

czech_bug_punishment = 0.5
ow_punishment = 0.5
diacritical_error_punishment = 0.5


def levensthein_dist(s1, s2):
    return edit_distance(s1, s2, transpositions=False)


TEST_WORD = None

diacritical_chars = {u'ą': u'a', u'ć': u'c', u'ę': u'e', u'ł': u'l', u'ń': u'n', u'ó': u'o', u'ś': u's', u'ź': u'z',
                     u'ż': u'z'}
diacritical_chars.update({v: k for k, v in diacritical_chars.iteritems()})


class LevenstheinWithRespectToErrors(object):
    def __init__(self):
        self.exceptions_ow = [u"skuwka", u"wsuwka", u"zasuwka"]

    def __call__(self, s1, s2):
        ops = editops(s1, s2)
        replacements = [(spos, dpos) for op_name, spos, dpos in ops if op_name == "replace"]
        count = 0
        for spos, dpos in replacements:
            if s1[spos] in diacritical_chars and diacritical_chars[s1[spos]] == s2[dpos]:
                count += 1
        base_dist = len(ops) - (1 - diacritical_error_punishment) * count
        base_dist -= self.find_all_occurrences_of_substring(u"uw", s1) * (1 - ow_punishment)
        return base_dist

    def find_all_occurrences_of_substring(self, sub_str, s1):
        index = 0
        count = 0
        if s1 in self.exceptions_ow:
            return count
        while index < len(s1):
            index = s1.find(sub_str, index)
            if index == -1:
                break
            count += 1
            index += len(sub_str)
        return count


def search_in_chunk(chunk):
    word = TEST_WORD
    smallest_dist = float("inf")
    best_matching_word = word
    metric = LevenstheinWithRespectToErrors()
    for train_word in chunk:
        dist = metric(word, train_word)
        if dist < smallest_dist:
            smallest_dist = dist
            best_matching_word = train_word
    return best_matching_word, smallest_dist


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


class WordCorrector(object):
    def __init__(self, metric, n_jobs=16):
        with codecs.open('data/formy_utf8.txt', 'r', 'utf-8') as f:
            self.words = [word for word in f.read().splitlines()]
        with open('data/formy.pkl', 'r') as f:
            self.words_hash = cPickle.load(f)
        self.metric = metric
        self.n_jobs = n_jobs

    def correct_words(self, words):
        return [self.find_closest(word) for word in words]

    def find_closest(self, test_word):
        if test_word in self.words:
            return test_word
        global TEST_WORD
        TEST_WORD = test_word
        smallest_dist = float("inf")
        best_matching_word = None
        first_letter = test_word[0]
        second_letter = test_word[1]

        words_to_search = self.words_hash[first_letter] + self.words_hash[second_letter]

        chunk_size = int(len(words_to_search) / self.n_jobs)

        arguments = list(chunks(words_to_search, chunk_size))

        p = Pool(self.n_jobs)
        results = p.map(search_in_chunk, arguments)
        p.close()
        p.join()

        for word, val in results:
            if val < smallest_dist:
                best_matching_word = word
                smallest_dist = val

        return best_matching_word


def get_word_corrector_with_respect_to_errors():
    metric = LevenstheinWithRespectToErrors()
    return WordCorrector(metric)


def get_word_corrector_with_levensthein_distance():
    return WordCorrector(levensthein_dist)


if __name__ == "__main__":
    word_corrector = get_word_corrector_with_respect_to_errors()
    word_to_be_corrected = u"pięśc"
    import time

    print "correcting..."
    start = time.time()
    print word_corrector.correct_words([word_to_be_corrected])
    end = time.time()
    print "correction took %f" % (end - start)
