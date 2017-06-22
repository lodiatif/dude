import os
import re
import uuid

from nltk.stem.snowball import SnowballStemmer

_ns = os.environ.get('DUDE_NAMESPACE', 'default')
_store = os.environ.get('DUDE_DB', 'dudefile.db')
_store_del = _store + ".deleted"

_BEGIN_MARKER = "====<BR %s>===="
_BEGIN_MARKER_RE = "====<BR (.*)>===="
_END_MARKER = "====<ER>===="


class Secret:
    def serialize(self, sid, key, secret, derived_keys=[], fuzzy_keys=[], username=None):
        self.sid = sid
        self.username = username if username else ''
        self.key = key
        self.secret = secret
        self.derived_keys = derived_keys
        self.fuzzy_keys = fuzzy_keys

        return "\n".join(
            [_BEGIN_MARKER % sid, self.username, self.key, " ".join(self.derived_keys + self.fuzzy_keys), self.secret,
             _END_MARKER])

    def deserialize(self, record):
        _bm, self.username, self.key, _keys, *_secret, _em = record.split("\n")
        if not self.username:
            self.username = None
        self.sid = re.search(_BEGIN_MARKER_RE, _bm).group(1)
        _keys = _keys.split()
        _mid = int(len(_keys) / 2)
        self.secret = "\n".join(_secret)
        self.derived_keys, self.fuzzy_keys = _keys[:_mid], _keys[_mid:]
        return self


def put(key, secret, username=None):
    """
    Store a secret and associate it with derived key words.
    The key parameter is split and every word (excluding stop words) is associated with the secret along with a
    matching strength score.

    :param username: user name
    :param key: key as provided by end-user
    :param secret: secret content
    :return: a tuple containing derived key words and the secret's ID assigned in database
    """
    key = key.lower()
    keys = _explode(key)
    orig_keys, stemmed_keys = list(zip(*keys)) if keys else ([], [])
    obj = Secret()
    record = obj.serialize(uuid.uuid4(), key, secret, orig_keys, stemmed_keys, username=username)
    with open(_store, "a") as f:
        f.write("\n%s" % record)
    return [obj.key] + obj.derived_keys, obj.sid


def remove(secret_id):
    """
    Forget a secret.

    :param secret_id: secret's ID
    """
    with open(_store_del, "a") as f:
        f.write("%s\n" % str(secret_id))


def get(key, username=None):
    """
    Get a collection of secrets associated with the key.

    :param username: user name
    :param key: the key
    :return: a list of tuples containing the following: secret ID, key, secret, score
    """
    key_set = set()
    secrets = []
    with open(_store_del, "r") as d:
        _deleted = set(d.read().split("\n"))
    with open(_store, "r") as f:
        for l in f:
            match = re.search(_BEGIN_MARKER_RE, l.strip())
            if match:
                secret_id = match.groups()[0]
                _username = f.readline().strip()
                if secret_id not in _deleted:
                    if username and _username != username or not username and _username:
                        continue
                    key_set.add(f.readline().strip())
                    key_set = key_set.union(f.readline().strip().split(" "))
                    if key.lower() in key_set:
                        secret_tokens = []
                        for l in f:
                            if l.strip() == _END_MARKER:
                                break
                            secret_tokens.append(l.strip())
                        secrets.append((secret_id, key, "\n".join(secret_tokens), 0))

    return secrets


def list_absolute_keys(username=None):
    """
    Get a collection of keys (tags) that have a score of 1 - essentially keys input by end-user while storing secrets.

    :param username: user name
    :return: a list of absolute keys
    """
    keys = []
    with open(_store_del, "r") as d:
        _deleted = set(d.read().split("\n"))
    with open(_store, "r") as f:
        for l in f:
            match = re.search(_BEGIN_MARKER_RE, l.strip())
            if match:
                secret_id = match.groups()[0]
                _username = f.readline().strip()
                if username and username != _username:
                    continue
                if secret_id not in _deleted:
                    keys.append(f.readline().strip())
    return keys


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
_stop_words = {"a", "is", "a's", "able", "about", "above", "according", "accordingly", "across", "actually", "after",
               "afterwards",
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

# keys, secret_id = put("here is my mobile number", "multi line\nmobile\n9867")
# remove(secret_id)
# print(get("here is my mobile number"))
