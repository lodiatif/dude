import os
from datetime import datetime

from src import da
from src.stores import file as filestore
from src.stores.file import Secret


class TestDA:
    @classmethod
    def setup_class(cls):
        cls.test_db = '_testfile.db'
        cls.username = '__tE5tE7__'
        open(cls.test_db, "w")
        open(cls.test_db + ".deleted", "w")
        filestore._store = cls.test_db
        filestore._store_del = cls.test_db + ".deleted"

    @classmethod
    def teardown_class(cls):
        os.remove(cls.test_db)
        os.remove(cls.test_db + ".deleted")

    def test_secret_serialize(self):
        secret = Secret()
        op = secret.serialize("21", "foo", "bar\nsecret", ["foo"], ["foo"], "atif-user",
                              datetime(2017, 6, 27, 19, 35, 44, 239))
        assert op == """====<BR 21>====\natif-user\n2017-06-27 19:35:44.000239\nfoo\nfoo foo\nbar\nsecret\n====<ER>===="""

    def test_secret_deserialize(self):
        secret = Secret()
        rec = """====<BR 21>====\natif-user\n2017-06-27 19:35:44.000239\nfoo\n\nbar\nsecret\n====<ER>====""".split("\n")
        secret = secret.deserialize(rec)
        assert secret.sid == "21" and secret.secret == "bar\nsecret"

    def test_put_get_remove(self):
        k, s = "foo", "bar"
        da.put(k, s, TestDA.username)
        secrets = da.get(k, TestDA.username)
        assert secrets[0][2] == s
        da.remove(secrets[0][0], TestDA.username)
        secrets = da.get(k, TestDA.username)
        assert secrets == []

    def test_put_stopword_key(self):
        k, s = "a", "to z"
        da.put(k, s, TestDA.username)
        secrets = da.get(k, TestDA.username)
        assert secrets[0][2] == s

    def test_one_key_many_secrets(self):
        da.put("knock knock joke", "sure!", TestDA.username)
        da.put("knock knock", "who is it?", TestDA.username)
        secrets = da.get('knock', TestDA.username)
        assert len(secrets) == 2

    def test_fuzzy_search(self):
        k, s = "this is my mobile number", "9867111111"
        da.put(k, s, TestDA.username)
        secrets = da.get("mobil", TestDA.username)
        assert secrets[0][2] == s

    def test_list_absolute_keys(self):
        k, s = "Lorem Ipsum", "no more a secret"
        da.put(k, s, TestDA.username)
        keys = da.list_absolute_keys(TestDA.username)
        assert k.lower() in keys

    def test_key_with_dash(self):
        keys, secret_id = da.put("mid-day", "newspaper?", TestDA.username)
        assert len(keys) == 3

    def test_username_filter(self):
        da.put("threads", "GIL!", username="python")
        da.put("threads", "multi", username="java")
        python_threads = da.get("threads", "python")
        java_threads = da.get("threads", "java")
        assert python_threads[0][2] == 'GIL!' and java_threads[0][2] == 'multi'

    def test_other_user_key(self):
        da.put("bank", "money", username="hardworker")
        secret = da.get("bank", username="hacker")
        assert secret == []
