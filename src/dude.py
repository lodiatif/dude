from src import da


def keep(secret, key):
    return da.put(key, secret)


def tell(tag):
    secrets = da.get(tag)
    return secrets


def list_absolute_keys():
    return da.list_absolute_keys()
