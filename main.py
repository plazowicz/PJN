# coding=utf-8
import cPickle
from multiprocessing import Pool

__author__ = 'mateuszopala'

czech_bug_punishment = 0.5
ow_punishment = 0.5
diacritical_error_punishment = 0.5


def levensthein_dist(s1, s2):
    return edit_distance(s1, s2, transpositions=False)


TEST_WORD = None

diacritical_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']


def _edit_dist_init(len1, len2):
    lev = []
    for i in range(len1):
        lev.append([0] * len2)  # initialize 2D array to zero
    for i in range(len1):
        lev[i][0] = i  # column 0: 0,1,2,3,4,...
    for j in range(len2):
        lev[0][j] = j  # row 0: 0,1,2,3,4,...
    return lev


def _edit_dist_step(lev, i, j, s1, s2, transpositions=False, transposition_punishment=0.5):
    c1 = s1[i - 1]
    c2 = s2[j - 1]

    # skipping a character in s1
    a = lev[i - 1][j] + 1
    # skipping a character in s2
    b = lev[i][j - 1] + 1
    # substitution
    c = lev[i - 1][j - 1] + (c1 != c2)

    # transposition
    d = c + 1  # never picked by default
    if transpositions and i > 1 and j > 1:
        if s1[i - 2] == c2 and s2[j - 2] == c1:
            d = lev[i - 2][j - 2] + transposition_punishment
    # global diacritical_chars
    # global diacritical_error_punishment
    # if c < a and c < b and c < d and c in diacritical_chars:
    #     c -= diacritical_error_punishment
    # pick the cheapest
    lev[i][j] = min(a, b, c, d)


def edit_distance(s1, s2, transpositions=False, transposition_punishment=0.5):
    """
    Calculate the Levenshtein edit-distance between two strings.
    The edit distance is the number of characters that need to be
    substituted, inserted, or deleted, to transform s1 into s2.  For
    example, transforming "rain" to "shine" requires three steps,
    consisting of two substitutions and one insertion:
    "rain" -> "sain" -> "shin" -> "shine".  These operations could have
    been done in other orders, but at least three steps are needed.

    This also optionally allows transposition edits (e.g., "ab" -> "ba"),
    though this is disabled by default.

    :param s1, s2: The strings to be analysed
    :param transpositions: Whether to allow transposition edits
    :type s1: str
    :type s2: str
    :type transpositions: bool
    :rtype int
    """
    # set up a 2-D array
    len1 = len(s1)
    len2 = len(s2)
    lev = _edit_dist_init(len1 + 1, len2 + 1)

    # iterate over the array
    for i in range(len1):
        for j in range(len2):
            _edit_dist_step(lev, i + 1, j + 1, s1, s2, transpositions=transpositions,
                            transposition_punishment=transposition_punishment)
    return lev[len1][len2]


class LevenstheinWithRespectToErrors(object):
    def __init__(self):
        self.exceptions_ow = ["skuwka", "wsuwka", "zasuwka"]

    def __call__(self, s1, s2):
        base_dist = edit_distance(s1, s2, transpositions=True, transposition_punishment=czech_bug_punishment)
        base_dist -= self.find_all_occurrences_of_substring("uw", s1) * (1 - ow_punishment)
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
        with open('data/formy_utf8.txt', 'r') as f:
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


# TODO ogarnac diakrytyczne i odpalic na softlayer

def get_word_corrector_with_respect_to_errors():
    metric = LevenstheinWithRespectToErrors()
    return WordCorrector(metric)


def get_word_corrector_with_levensthein_distance():
    return WordCorrector(levensthein_dist)


if __name__ == "__main__":
    word_corrector = get_word_corrector_with_respect_to_errors()
    word_to_be_corrected = u"mąma"
    import time

    print "correcting..."
    start = time.time()
    print word_corrector.correct_words([word_to_be_corrected])
    end = time.time()
    print "correction took %f" % (end - start)
