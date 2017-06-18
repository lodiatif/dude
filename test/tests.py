import os

from nose.tools import assert_raises

from src import da
from src.da import get, remove
from src.da import put
from src.store import Store, DuplicityError


class TestStore():
    @classmethod
    def setup_class(cls):
        cls.db_name = ':memory:'
        cls.secret = "This is a secret"

    def test_put_secret(self):
        with Store(TestStore.db_name) as db:
            db._create()
            secret_id = db.put_secret(TestStore.secret)
            secret_text = db.get_secret(secret_id)
            assert secret_text == TestStore.secret

    def test_remove_secret(self):
        with Store(TestStore.db_name) as db:
            db._create()
            secret_id = db.put_secret(TestStore.secret)
            db.remove_secret(secret_id)
            secret_text = db.get_secret(secret_id)
            assert secret_text is None

    def test_get_secret_id(self):
        with Store(TestStore.db_name) as db:
            db._create()
            db.put_secret(TestStore.secret)
            assert (1 == db.get_secret_id_by_text(TestStore.secret))

    def test_get_absent_secret(self):
        with Store(TestStore.db_name) as db:
            db._create()
            assert (None == db.get_secret_id_by_text(TestStore.secret))

    def test_duplicate_secret(self):
        with Store(TestStore.db_name) as db:
            db._create()
            db.put_secret(TestStore.secret)
            assert_raises(DuplicityError, db.put_secret, TestStore.secret)

    def test_map_keys_secret(self):
        with Store(TestStore.db_name) as db:
            db._create()
            db.put_secret(TestStore.secret)
            db.map_keys_secret(1, ["hello", ], [0.3, ])
            assert (db.get_secrets_by_key('hello') == [(1, 'hello', 'This is a secret', 0.3)])

    def test_cascade(self):
        with Store(TestStore.db_name) as db:
            db._create()
            secret_id = db.put_secret(TestStore.secret)
            db.map_keys_secret(secret_id, ['foo', 'bar'], [0.5, 0.5])
            db.remove_secret(secret_id)
            assert db.get_secrets_by_key('foo') == []


class TestDA:
    @classmethod
    def setup_class(cls):
        da._DB_NAME = '_test_db.db'
        with Store(da._DB_NAME) as store:
            store._create()

    @classmethod
    def teardown_class(cls):
        os.remove('_test_db.db')

    def test_put_secret(self):
        keys, secret_id = put("tell you a secret?", "coffee")
        assert len(keys) == 3 and secret_id is not None

    def test_one_key_many_secrets(self):
        put("knock knock joke", "sure!")
        put("knock knock", "who is it?")
        secrets = get('knock')
        assert len(secrets) == 2

    def test_remove_secret(self):
        k, secret_id = put("thou shall be perished", "sigh!")
        remove(secret_id)
        secrets = get('removed')
        assert secrets == []

    def test_key_with_dash(self):
        keys, secret_id = put("mid-day", "newspaper?")
        assert len(keys) == 3
