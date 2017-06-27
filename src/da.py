import os

import sys

_storage = os.environ.get("DUDE_STORE", "file")
if _storage.lower() == "file":
    print("[Using file as storage]")
    from src.stores import file as store
elif _storage.lower() == "mongodb":
    print("[Using mongodb as storage]")
    from src.stores import mongodb as store
else:
    print("Storage %s not supported" % _storage)
    sys.exit(1)

from nltk.stem.snowball import SnowballStemmer


def put(key, secret, username):
    """
    Store a secret and associate it with derived key words.
    The key parameter is split and every word (excluding stop words) is associated with the secret along with a
    matching strength score.

    :param key: key as provided by end-user
    :param secret: secret content
    :param username: user name
    :return: a tuple containing derived key words and the secret's ID assigned in database
    """
    key = key.lower()
    keys = _explode(key)
    derived_keys, stemmed_keys = list(zip(*keys)) if keys else ([], [])
    secret_id = store.put(secret, key, derived_keys, stemmed_keys, username)
    return set([key] + list(derived_keys) + list(stemmed_keys)), secret_id


def remove(secret_id, username):
    """
    Forget a secret.

    :param secret_id: secret's ID
    :param username: user name
    """
    store.remove(secret_id, username)


def get(key, username):
    """
    Get a collection of secrets associated with the key.

    :param username: user name
    :param key: the key
    :return: a list of tuples containing the following: secret ID, original key, secret content, timestamp
    """
    key = key.lower()
    return store.get(key, username)


def list_absolute_keys(username):
    """
    Get a collection of keys (tags) that have a score of 1 - essentially keys input by end-user while storing secrets.

    :param username: user name
    :return: a list of absolute keys
    """
    return store.get_keys(username)


def _explode(key):
    """
    Derives all possible keywords from input key. All the stop words are excluded.

    :param key: key as provided by end-user
    :return: list of tuples containing original and stemmed words
    """
    key = key.lower()
    words = set(key.split())
    derived_keys = set()
    for word in words:
        ret = _stem(word)
        for ok, k in ret:
            derived_keys.add((ok, k))
    keys = list(derived_keys)
    return keys


# TODO externalize stop words
_stop_words = {"-", "_", "a", "is", "a's", "able", "about", "above", "according", "accordingly", "across", "actually",
               "after", "afterwards",
               "again", "against", "ain't", "all", "allow", "allows", "almost", "alone", "along", "already", "also",
               "although", "always", "am", "among", "amongst", "an", "and", "another", "any", "anybody", "anyhow",
               "anyone", "anything", "anyway", "anyways", "anywhere", "apart", "appear", "appreciate", "appropriate",
               "are", "aren't", "around", "as", "aside", "ask", "asking", "associated", "at", "available", "away",
               "awfully", "be", "became", "because", "become", "becomes", "becoming", "been", "before", "beforehand",
               "behind", "being", "believe", "below", "beside", "besides", "best", "better", "between", "beyond",
               "both", "brief", "but", "by", "c'mon", "c's", "came", "can", "can't", "cannot", "cant", "cause",
               "causes", "certain", "certainly", "changes", "clearly", "co", "com", "come", "comes", "concerning",
               "consequently", "consider", "considering", "contain", "containing", "contains", "corresponding", "could",
               "couldn't", "course", "currently", "definitely", "described", "despite", "did", "didn't", "different",
               "do", "does", "doesn't", "doing", "don't", "done", "down", "downwards", "during", "each", "edu", "eg",
               "eight", "either", "else", "elsewhere", "enough", "entirely", "especially", "et", "etc", "even", "ever",
               "every", "everybody", "everyone", "everything", "everywhere", "ex", "exactly", "example", "except",
               "far", "few", "fifth", "first", "five", "followed", "following", "follows", "for", "former", "formerly",
               "forth", "four", "from", "further", "furthermore", "get", "gets", "getting", "given", "gives", "go",
               "goes", "going", "gone", "got", "gotten", "greetings", "had", "hadn't", "happens", "hardly", "has",
               "hasn't", "have", "haven't", "having", "he", "he's", "hello", "help", "hence", "her", "here", "here's",
               "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "hi", "him", "himself", "his", "hither",
               "hopefully", "how", "howbeit", "however", "i'd", "i'll", "i'm", "i've", "ie", "if", "ignored",
               "immediate", "in", "inasmuch", "inc", "indeed", "indicate", "indicated", "indicates", "inner", "insofar",
               "instead", "into", "inward", "is", "isn't", "it", "it'd", "it'll", "it's", "its", "itself", "just",
               "keep", "keeps", "kept", "know", "known", "knows", "last", "lately", "later", "latter", "latterly",
               "least", "less", "lest", "let", "let's", "like", "liked", "likely", "little", "look", "looking", "looks",
               "ltd", "mainly", "many", "may", "maybe", "me", "mean", "meanwhile", "merely", "might", "more",
               "moreover", "most", "mostly", "much", "must", "my", "myself", "name", "namely", "nd", "near", "nearly",
               "necessary", "need", "needs", "neither", "never", "nevertheless", "new", "next", "nine", "no", "nobody",
               "non", "none", "noone", "nor", "normally", "not", "nothing", "novel", "now", "nowhere", "obviously",
               "of", "off", "often", "oh", "ok", "okay", "old", "on", "once", "one", "ones", "only", "onto", "or",
               "other", "others", "otherwise", "ought", "our", "ours", "ourselves", "out", "outside", "over", "overall",
               "own", "particular", "particularly", "per", "perhaps", "placed", "please", "plus", "possible",
               "presumably", "probably", "provides", "que", "quite", "qv", "rather", "rd", "re", "really", "reasonably",
               "regarding", "regardless", "regards", "relatively", "respectively", "right", "said", "same", "saw",
               "say", "saying", "says", "second", "secondly", "see", "seeing", "seem", "seemed", "seeming", "seems",
               "seen", "self", "selves", "sensible", "sent", "serious", "seriously", "seven", "several", "shall", "she",
               "should", "shouldn't", "since", "six", "so", "some", "somebody", "somehow", "someone", "something",
               "sometime", "sometimes", "somewhat", "somewhere", "soon", "sorry", "specified", "specify", "specifying",
               "still", "sub", "such", "sup", "sure", "t's", "take", "taken", "tell", "tends", "th", "than", "thank",
               "thanks", "thanx", "that", "that's", "thats", "the", "their", "theirs", "them", "themselves", "then",
               "thence", "there", "there's", "thereafter", "thereby", "therefore", "therein", "theres", "thereupon",
               "these", "they", "they'd", "they'll", "they're", "they've", "think", "third", "this", "thorough",
               "thoroughly", "those", "though", "three", "through", "throughout", "thru", "thus", "to", "together",
               "too", "took", "toward", "towards", "tried", "tries", "truly", "try", "trying", "twice", "two", "un",
               "under", "unfortunately", "unless", "unlikely", "until", "unto", "up", "upon", "us", "use", "used",
               "useful", "uses", "using", "usually", "value", "various", "very", "via", "viz", "vs", "want", "wants",
               "was", "wasn't", "way", "we", "we'd", "we'll", "we're", "we've", "welcome", "well", "went", "were",
               "weren't", "what", "what's", "whatever", "when", "whence", "whenever", "where", "where's", "whereafter",
               "whereas", "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who",
               "who's", "whoever", "whole", "whom", "whose", "why", "will", "willing", "wish", "with", "within",
               "without", "won't", "wonder", "would", "wouldn't", "yes", "yet", "you", "you'd", "you'll", "you're",
               "you've", "your", "yours", "yourself", "yourselves", "zero", }


def _stem(word):
    # TODO - handle dashed words. return list of words since one word could lead to 2 or more
    word = word.replace("'", "").replace("?", "")
    in_word_set = {word}.union(word.split("-"))
    out_word_set = set()
    stemmer = SnowballStemmer("english")
    for word in in_word_set:
        if word not in _stop_words:
            out_word_set.add((word, stemmer.stem(word)))
    return out_word_set
