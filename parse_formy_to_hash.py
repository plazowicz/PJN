__author__ = 'mateuszopala'
from collections import defaultdict
import cPickle
import codecs


if __name__ == "__main__":
    with codecs.open('data/formy_utf8.txt', 'r', 'utf-8') as f:
        words = f.read().splitlines()
    words_dict = defaultdict(list)
    for word in words:
        words_dict[word[0]].append(word)

    with open('data/formy.pkl', 'w') as f:
        cPickle.dump(words_dict, f)
