import os
import sqlite3


class Store():
    def __init__(self, name):
        self.conn = sqlite3.connect(name)
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _create(self):
        """
        Create tables needed for dude app.
        """
        with self.conn:
            self.conn.execute('''CREATE TABLE secret
                         (id integer PRIMARY KEY, secret_text text UNIQUE)''')

            self.conn.execute('''CREATE TABLE key_secret (key text, secret_id int, score real,
                         map_time timestamp DEFAULT CURRENT_TIMESTAMP,
                         FOREIGN KEY(secret_id) REFERENCES secret(id) on delete cascade,
                         UNIQUE (key, secret_id))''')

    def put_secret(self, secret):
        """
        Persist a 'secret' content.

        :param secret: secret content
        :return: ID of the secret content created
        :raises: DuplicityError in case the content already exist
        """
        try:
            with self.conn:
                cursor = self.conn.execute("INSERT INTO secret (secret_text) VALUES (?)", (secret,))
                return cursor.lastrowid
        except sqlite3.IntegrityError as ie:
            if str(ie) == 'UNIQUE constraint failed: secret.secret_text':
                raise DuplicityError(ie)
            else:
                raise

    def get_secret(self, secret_id):
        """
        Fetch secret content by its ID.

        :param secret_id: secret's ID
        :return: secret content if found, None otherwise
        """
        with self.conn:
            cursor = self.conn.execute("SELECT secret_text FROM secret WHERE id = ?", (secret_id,))
            secret_text = cursor.fetchone()
        return secret_text[0] if secret_text else secret_text

    def get_secret_id_by_text(self, secret):
        """
        Get secret content's ID.

        :param secret: secret content
        :return: secret' ID if secret found, None otherwise
        """
        with self.conn:
            cursor = self.conn.execute("SELECT id FROM secret WHERE secret_text = ?", (secret,))
            id = cursor.fetchone()
        return id[0] if id else id

    def map_keys_secret(self, secret_id, keys, scores):
        """
        Associate keys (tags) with a secret along with their match strength score.

        :param secret_id: secret's ID
        :param keys: collection of key words
        :param scores: match strength score
        """
        with self.conn:
            self.conn.executemany("INSERT OR REPLACE INTO key_secret (key, secret_id, score) VALUES (?, ?, ?)",
                                  [(key, secret_id, score) for key, score in zip(keys, scores)])

    def get_secrets_by_key(self, key):
        """
        Fetch a collection of secrets associated with the key-word.

        :param key: the key word associated with secrets
        :return: a list of tuples containing the following: secret ID, key, secret, score
        """
        with self.conn:
            cursor = self.conn.execute("SELECT secret_id, key, secret_text, score FROM secret s JOIN key_secret ks "
                                       "ON s.id = ks.secret_id WHERE ks.key = ?",
                                       (key,))
            secrets = cursor.fetchall()
        return secrets

    def remove_secret(self, secret_id):
        """
        Remove a secret.

        :param secret_id: secret's ID
        """
        with self.conn:
            self.conn.execute("DELETE FROM secret WHERE id = ?", (secret_id,))

    def list_absolute_keys(self):
        """
        Get all keys that have score as 1 - original input from end-user.
        """
        with self.conn:
            cursor = self.conn.execute("SELECT key FROM key_secret WHERE score = 1")
            keys = cursor.fetchall()
        return keys

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class FileStore():
    def __init__(self, name):
        self.file_name = name
        self.conn = open(self.file_name, 'a+b')

    def _create(self):
        if not os.path.isfile(self.file_name):
            open(self.file_name, 'a')

    def put_secret(self, secret):
        """
        Persist a 'secret' content.

        :param secret: secret content
        :return: ID of the secret content created
        :raises: DuplicityError in case the content already exist
        """
        try:
            with open(self.file_name, 'a') as f:

                cursor = self.conn.execute("INSERT INTO secret (secret_text) VALUES (?)", (secret,))
                return cursor.lastrowid
        except sqlite3.IntegrityError as ie:
            if str(ie) == 'UNIQUE constraint failed: secret.secret_text':
                raise DuplicityError(ie)
            else:
                raise

    def get_secret(self, secret_id):
        """
        Fetch secret content by its ID.

        :param secret_id: secret's ID
        :return: secret content if found, None otherwise
        """
        with self.conn:
            cursor = self.conn.execute("SELECT secret_text FROM secret WHERE id = ?", (secret_id,))
            secret_text = cursor.fetchone()
        return secret_text[0] if secret_text else secret_text

    def get_secret_id_by_text(self, secret):
        """
        Get secret content's ID.

        :param secret: secret content
        :return: secret' ID if secret found, None otherwise
        """
        with self.conn:
            cursor = self.conn.execute("SELECT id FROM secret WHERE secret_text = ?", (secret,))
            id = cursor.fetchone()
        return id[0] if id else id

    def map_keys_secret(self, secret_id, keys, scores):
        """
        Associate keys (tags) with a secret along with their match strength score.

        :param secret_id: secret's ID
        :param keys: collection of key words
        :param scores: match strength score
        """
        with self.conn:
            self.conn.executemany("INSERT OR REPLACE INTO key_secret (key, secret_id, score) VALUES (?, ?, ?)",
                                  [(key, secret_id, score) for key, score in zip(keys, scores)])

    def get_secrets_by_key(self, key):
        """
        Fetch a collection of secrets associated with the key-word.

        :param key: the key word associated with secrets
        :return: a list of tuples containing the following: secret ID, key, secret, score
        """
        with self.conn:
            cursor = self.conn.execute("SELECT secret_id, key, secret_text, score FROM secret s JOIN key_secret ks "
                                       "ON s.id = ks.secret_id WHERE ks.key = ?",
                                       (key,))
            secrets = cursor.fetchall()
        return secrets

    def remove_secret(self, secret_id):
        """
        Remove a secret.

        :param secret_id: secret's ID
        """
        with self.conn:
            self.conn.execute("DELETE FROM secret WHERE id = ?", (secret_id,))

    def list_absolute_keys(self):
        """
        Get all keys that have score as 1 - original input from end-user.
        """
        with self.conn:
            cursor = self.conn.execute("SELECT key FROM key_secret WHERE score = 1")
            keys = cursor.fetchall()
        return keys

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DuplicityError(Exception):
    pass
