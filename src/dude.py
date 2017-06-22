from src import file_da as da


def keep(secret, key, username=None):
    return da.put(key, secret, username)


def tell(tag, username=None):
    secrets = da.get(tag, username)
    return secrets


def list_absolute_keys(username=None):
    return da.list_absolute_keys(username)
