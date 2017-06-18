import sqlite3


class Store():
    def __init__(self, name, atomic=True):
        self.conn = sqlite3.connect(name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.atomic = atomic
        self.errored = False

    def _create(self):
        """
        Create tables needed for dude app.
        """
        c = self.conn.cursor()
        c.execute('''CREATE TABLE secret
                     (id integer PRIMARY KEY, secret_text text UNIQUE)''')

        c.execute('''CREATE TABLE key_secret (key text, secret_id int, score real,
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
        sql = "INSERT INTO secret (secret_text) VALUES (?)"
        c = self.conn.cursor()
        try:
            c.execute(sql, (secret,))
        except sqlite3.IntegrityError as ie:
            if str(ie) == 'UNIQUE constraint failed: secret.secret_text':
                raise DuplicityError(ie)
            else:
                raise
        c.close()
        return c.lastrowid

    def get_secret(self, secret_id):
        """
        Fetch secret content by its ID.

        :param secret_id: secret's ID
        :return: secret content if found, None otherwise
        """
        sql = "SELECT secret_text FROM secret WHERE id = ?"
        c = self.conn.cursor()
        c.execute(sql, (secret_id,))
        secret_text = c.fetchone()
        c.close()
        return secret_text[0] if secret_text else secret_text

    def get_secret_id_by_text(self, secret):
        """
        Get secret content's ID.

        :param secret: secret content
        :return: secret' ID if secret found, None otherwise
        """
        sql = "SELECT id FROM secret WHERE secret_text = ?"
        c = self.conn.cursor()
        c.execute(sql, (secret,))
        id = c.fetchone()
        c.close()
        return id[0] if id else id

    def map_keys_secret(self, secret_id, keys, scores):
        """
        Associate keys (tags) with a secret along with their match strength score.

        :param secret_id: secret's ID
        :param keys: collection of key words
        :param scores: match strength score
        """
        sql = "INSERT OR REPLACE INTO key_secret (key, secret_id, score) VALUES (?, ?, ?)"
        c = self.conn.cursor()
        c.executemany(sql, [(key, secret_id, score) for key, score in zip(keys, scores)])
        c.close()

    def get_secrets_by_key(self, key):
        """
        Fetch a collection of secrets associated with the key-word.

        :param key: the key word associated with secrets
        :return: a list of tuples containing the following: secret ID, key, secret, score
        """
        sql = "SELECT secret_id, key, secret_text, score FROM secret s JOIN key_secret ks ON s.id = ks.secret_id " \
              "WHERE ks.key = ?"
        c = self.conn.cursor()
        c.execute(sql, (key,))
        secrets = c.fetchall()
        c.close()
        return secrets

    def remove_secret(self, secret_id):
        """
        Remove a secret.

        :param secret_id: secret's ID
        """
        sql = "DELETE FROM secret WHERE id = ?"
        c = self.conn.cursor()
        c.execute(sql, (secret_id,))
        c.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.errored and self.atomic:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()


class DuplicityError(Exception):
    pass
