import csv
import os
import re
import uuid
from datetime import datetime

_ns = os.environ.get('DUDE_NAMESPACE', 'default')
_store = os.environ.get('DUDE_FILE_DB', 'dudefile.db') + "_" + _ns
_store_del = _store + ".deleted"

_BEGIN_MARKER = "====<BR %s>===="
_BEGIN_MARKER_RE = "====<BR (.*)>===="
_END_MARKER = "====<ER>===="


class Secret:
    def serialize(self, sid, key, secret, derived_keys, fuzzy_keys, username, in_ts):
        self.sid = sid
        self.username = username if username else ''
        self.key = key
        self.secret = secret
        self.derived_keys = derived_keys
        self.fuzzy_keys = fuzzy_keys
        self.in_ts = in_ts

        return "\n".join(
            [_BEGIN_MARKER % sid, self.username, str(self.in_ts), self.key,
             " ".join(self.derived_keys + self.fuzzy_keys),
             self.secret, _END_MARKER])

    def deserialize(self, record):
        _bm, self.username, _ts, self.key, _keys, *_secret, _em = record
        if not self.username:
            self.username = None
        self.in_ts = datetime.strptime(_ts, "%Y-%m-%d %H:%M:%S.%f")
        self.sid = re.search(_BEGIN_MARKER_RE, _bm).group(1)
        _keys = _keys.split()
        _mid = int(len(_keys) / 2)
        self.secret = "\n".join(_secret)
        self.derived_keys, self.fuzzy_keys = _keys[:_mid], _keys[_mid:]
        return self

    def summary(self):
        return (self.sid, self.key, self.secret, self.in_ts)


def put(secret, orig_key, derived_keys, stemmed_keys, username):
    """
    Put a secret in store along with its key and derived keys.

    :param secret: secret content
    :param orig_key: original key
    :param derived_keys: split key words
    :param stemmed_keys: stemmed key words
    :param username: user name
    """
    obj = Secret()
    record = obj.serialize(uuid.uuid4(), orig_key, secret, derived_keys, stemmed_keys, username, datetime.utcnow())
    with open(_store, "a") as f:
        f.write("\n%s" % record)
    return obj.sid


def remove(secret_id, username):
    """
    Forget a secret.

    :param secret_id: secret's ID
    :param username: user name
    """
    row = [username, str(secret_id)]
    with open(_store_del, "a") as f:
        out = csv.writer(f)
        out.writerow(row)


def remove_all(username):
    """
    Forget a secret.

    :param username: user name
    """
    obj = Secret()
    for record in _cursor():
        obj = obj.deserialize(record)
        if obj.username == username:
            remove(obj.sid, username)


def _cursor():
    with open(_store, "r") as f:
        for l in f:
            record = []
            match = re.search(_BEGIN_MARKER_RE, l.strip())
            if match:
                record.append(l)
                record.append(f.readline().strip())  # username
                record.append(f.readline().strip())  # ts
                record.append(f.readline().strip())  # key
                record.append(f.readline().strip())  # derived keys
                for l in f:
                    record.append(l.strip())
                    if l.strip() == _END_MARKER:
                        break
            if record:
                yield record


def get(key, username):
    """
    Get a collection of secrets associated with the key.

    :param username: user name
    :param key: the key
    :return: a list of tuples containing the following: secret ID, key, secret, score
    """
    secrets = []
    _deleted = []
    with open(_store_del, "r") as d:
        for row in csv.reader(d):
            (_username, secret_id) = row
            if _username == username:
                _deleted.append(secret_id)
    obj = Secret()
    for record in _cursor():
        key_set = set()
        obj = obj.deserialize(record)
        if obj.sid not in _deleted:
            if obj.username == username:
                key_set.add(obj.key)
                key_set = key_set.union(obj.derived_keys)
                key_set = key_set.union(obj.fuzzy_keys)
                if key.lower() in key_set:
                    secrets.append(obj.summary())

    return secrets


def get_keys(username):
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
                _ts = f.readline().strip()
                if username != _username:
                    continue
                if secret_id not in _deleted:
                    keys.append(f.readline().strip())
    return keys


def _vacuum():
    pass


class TestFilestore:
    @classmethod
    def setup_class(cls):
        cls.username = "__tE5tE7__"

    @classmethod
    def teardown_class(cls):
        remove_all(cls.username)
        remove_all(cls.username + "_1")

    def test_put_get(self):
        key, secret = "mongodb", "document db"
        put(secret, key, [key, ], [key, ], TestFilestore.username)
        record = get(key, TestFilestore.username)[0]
        assert record[2] == secret

    def test_remove(self):
        key, secret = "perishable", "earth"
        _id = put(secret, key, [key, ], [key, ], TestFilestore.username)
        put(secret, key, [key, ], [key, ], TestFilestore.username + "_1")
        remove(_id, TestFilestore.username)
        assert len(get(key, TestFilestore.username)) == 0 and len(get(key, TestFilestore.username + "_1")) == 1

    def test_duplicate_key(self):
        key, secret1, secret2 = "double", "first", "second"
        put(secret1, key, [key, ], [key, ], TestFilestore.username)
        put(secret2, key, [key, ], [key, ], TestFilestore.username)
        result = get(key, TestFilestore.username)
        record = result[0]
        assert record[2] == secret1
        record = result[1]
        assert record[2] == secret2

    def test_get_by_username(self):
        key, secret = "linux", "open source OS"
        put(secret, key, [key, ], [key, ], TestFilestore.username)
        record = get(key, TestFilestore.username)[0]
        assert record[2] == secret

    def test_get_by_diff_username(self):
        key, secret, username = "linux", "open source OS", "hacker"
        put(secret, key, [key, ], [key, ], TestFilestore.username)
        assert len(get(key, username)) == 0

    def test_get_by_partial_key(self):
        key, secret = "foo bar", "horse ranch"
        put(secret, key, key.split(), key.split(), TestFilestore.username)
        record = get(key.split()[1], TestFilestore.username)[0]
        assert record[2] == secret

    def test_get_by_stemmed_key(self):
        key, secret = "running fox", "sleeping rabbit"
        stemmed_keys = ["run", "fox"]
        put(secret, key, key.split(), stemmed_keys, TestFilestore.username)
        record = get(stemmed_keys[0], TestFilestore.username)[0]
        assert record[2] == secret

    def test_get_keys(self):
        key, secret = "multi-word key", "ignored secret"
        put(secret, key, key.split(), key.split(), TestFilestore.username)
        keys = get_keys(TestFilestore.username)
        assert key in keys
