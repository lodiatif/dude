from src import da


def keep(secret, key, username):
    return da.put(key, secret, username)


def tell(tag, username):
    secrets = da.get(tag, username)
    return secrets


def list_absolute_keys(username):
    return da.list_absolute_keys(username)
