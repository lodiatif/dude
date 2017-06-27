import os
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient

_ns = os.environ.get('DUDE_NAMESPACE', 'default')
_client = MongoClient(os.environ.get('DUDE_MDB_URI', "mongodb://localhost:27017/"))
_db = _client[os.environ.get('DUDE_MDB_NAME', "dude") + "_" + _ns]
_collection = _db[os.environ.get('DUDE_MDB_COLLECTION', "secrets")]


def put(secret, orig_key, derived_keys, stemmed_keys, username):
    """
    Put a secret in store along with its key and derived keys.

    :param secret: secret content
    :param orig_key: original key
    :param derived_keys: split key words
    :param stemmed_keys: stemmed key words
    :param username: user name
    """
    insert_ts = datetime.utcnow()
    record = {"in_ts": insert_ts, "derived_keys": derived_keys, "stemmed_keys": stemmed_keys}
    filter = {"username": username, "key": orig_key, "secret": secret}
    record.update(filter)
    # db_response = _collection.replace_one(filter, record, upsert=True)
    db_response = _collection.insert(record)
    return str(db_response)


def get(key, username):
    condn = {"$or": [{"key": key},
                     {"derived_keys": {"$elemMatch": {"$eq": key}}},
                     {"stemmed_keys": {"$elemMatch": {"$eq": key}}},
                     ],
             "username": username
             }
    record_set = []
    for record in _collection.find(condn, {"secret": 1, "key": 1, "in_ts": 1, "_id": 1}):
        record_set.append((str(record['_id']), record['key'], record['secret'], record['in_ts']))
    return record_set


def get_keys(username):
    condn = {"username": username}
    record_set = set()
    for record in _collection.find(condn, {"key": 1, "_id": 1}):
        record_set.add(record['key'])
    return list(record_set)


def remove(secret_id, username):
    condn = {"_id": ObjectId(secret_id), "username": username}
    return _collection.remove(condn)


def remove_all(username):
    condn = {"username": username}
    return _collection.remove(condn)


class TestMongodb:
    @classmethod
    def setup_class(cls):
        cls.username = "__tE5tE7__"

    @classmethod
    def teardown_class(cls):
        remove_all(cls.username)
        remove_all(cls.username + "_1")

    def test_put_get(self):
        key, secret = "mongodb", "document db"
        put(secret, key, [key, ], [key, ], TestMongodb.username)
        record = get(key, TestMongodb.username)[0]
        assert record[2] == secret

    def test_remove(self):
        key, secret = "perishable", "earth"
        _id = put(secret, key, [key, ], [key, ], TestMongodb.username)
        put(secret, key, [key, ], [key, ], TestMongodb.username + "_1")
        remove(_id, TestMongodb.username)
        assert len(get(key, TestMongodb.username)) == 0 and len(get(key, TestMongodb.username + "_1")) == 1

    def test_duplicate_key(self):
        key, secret1, secret2 = "double", "first", "second"
        put(secret1, key, [key, ], [key, ], TestMongodb.username)
        put(secret2, key, [key, ], [key, ], TestMongodb.username)
        result = get(key, TestMongodb.username)
        record = result[0]
        assert record[2] == secret1
        record = result[1]
        assert record[2] == secret2

    def test_get_by_username(self):
        key, secret = "linux", "open source OS"
        put(secret, key, [key, ], [key, ], TestMongodb.username)
        record = get(key, TestMongodb.username)[0]
        assert record[2] == secret

    def test_get_by_diff_username(self):
        key, secret, username = "linux", "open source OS", "hacker"
        put(secret, key, [key, ], [key, ], TestMongodb.username)
        assert len(get(key, username)) == 0

    def test_get_by_partial_key(self):
        key, secret = "foo bar", "horse ranch"
        put(secret, key, key.split(), key.split(), TestMongodb.username)
        record = get(key.split()[1], TestMongodb.username)[0]
        assert record[2] == secret

    def test_get_by_stemmed_key(self):
        key, secret = "running fox", "sleeping rabbit"
        stemmed_keys = ["run", "fox"]
        put(secret, key, key.split(), stemmed_keys, TestMongodb.username)
        record = get(stemmed_keys[0], TestMongodb.username)[0]
        assert record[2] == secret

    def test_get_keys(self):
        key, secret = "multi-word key", "ignored secret"
        put(secret, key, key.split(), key.split(), TestMongodb.username)
        keys = get_keys(TestMongodb.username)
        assert key in keys
