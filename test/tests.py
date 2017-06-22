import os

from src import file_da
from src.file_da import Secret


class TestSecretDA:
    @classmethod
    def setup_class(cls):
        cls.test_db = '_testfile.db'
        file_da._store = cls.test_db
        open(cls.test_db, "w")
        open(cls.test_db + ".deleted", "w")

    @classmethod
    def teardown_class(cls):
        os.remove(cls.test_db)
        os.remove(cls.test_db + ".deleted")

    def test_secret_serialize(self):
        secret = Secret()
        op = secret.serialize("21", "foo", "bar\nsecret", username="atif-user")
        assert op == """====<BR 21>====\natif-user\nfoo\n\nbar\nsecret\n====<ER>===="""

    def test_secret_deserialize(self):
        secret = Secret()
        rec = """====<BR 21>====\natif-user\nfoo\n\nbar\nsecret\n====<ER>===="""
        secret = secret.deserialize(rec)
        assert secret.sid == "21" and secret.secret == "bar\nsecret"

    def test_put_get_remove(self):
        k, s = "foo", "bar"
        file_da.put(k, s)
        secrets = file_da.get(k)
        assert secrets[0][2] == s
        file_da.remove(secrets[0][0])
        secrets = file_da.get(k)
        assert secrets == []

    def test_put_stopword_key(self):
        k, s = "a", "to z"
        file_da.put(k, s)
        secrets = file_da.get(k)
        assert secrets[0][2] == s

    def test_one_key_many_secrets(self):
        file_da.put("knock knock joke", "sure!")
        file_da.put("knock knock", "who is it?")
        secrets = file_da.get('knock')
        assert len(secrets) == 2

    def test_fuzzy_search(self):
        k, s = "this is my mobile number", "9867111111"
        file_da.put(k, s)
        secrets = file_da.get("mobil")
        assert secrets[0][2] == s

    def test_list_absolute_keys(self):
        k, s = "Lorem Ipsum", "no more a secret"
        file_da.put(k, s)
        keys = file_da.list_absolute_keys()
        assert k.lower() in keys

    def test_key_with_dash(self):
        keys, secret_id = file_da.put("mid-day", "newspaper?")
        assert len(keys) == 3

    def test_username_filter(self):
        file_da.put("threads", "GIL!", username="python")
        file_da.put("threads", "multi", username="java")
        python_threads = file_da.get("threads", "python")
        java_threads = file_da.get("threads", "java")
        assert python_threads[0][2] == 'GIL!' and java_threads[0][2] == 'multi'

    def test_other_user_key(self):
        file_da.put("bank", "money", username="hardworker")
        secret = file_da.get("bank", "hacker")
        assert secret == []

    def test_user_none(self):
        file_da.put("boy", "toys", username="father")
        file_da.put("boy", "hungry")
        secret1 = file_da.get("boy", "father")
        secret2 = file_da.get("boy")
        assert secret1[0][2] == "toys" and secret2[0][2] == "hungry"
