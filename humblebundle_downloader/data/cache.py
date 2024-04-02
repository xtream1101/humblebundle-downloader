from typing import Iterator
from base64 import b16encode

CSV_CACHE: str = "cache.csv"


def make_key(order_id: str, filename: str, trove: bool = False) -> str:
    return f"{order_id}:{str(b16encode(str.encode(filename)))[2:-1]}:{str(int(trove))}"


def _strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    if None is val:
        return False
    val = str(val).lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0', 'none'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))


def _strtonone(val):
    val = str(val).lower()
    if val == 'none':
        return None
    else:
        raise ValueError("value was none 'None' %r" % (val,))

class CacheDataJson:
    key: str
    value: dict

    def __init__(self, key: str, value: dict):
        self.key = key
        self.value = value


class CsvCacheData:

    def __init__(self, order_id: str,
                 filename: str,
                 md5: str = None,
                 remote_modified_date: str = None,
                 local_modified_date: str = None,
                 trove: bool = False
                 ):
        trove = _strtobool(trove)
        self.key = make_key(order_id, filename, trove)
        self.order_id = order_id
        self.filename = filename
        self.md5 = md5
        self.remote_modified_date = remote_modified_date
        self.local_modified_date = local_modified_date
        self.trove = trove

    def set_remote_modified_date(self, remote_modified_date: str):
        self.remote_modified_date = remote_modified_date

    def set_local_modified_date(self, local_modified_date: str):
        self.local_modified_date = local_modified_date

    def set_md5(self, md5: str):
        self.md5 = md5

    def __str__(self):
        return (f"{self.key},{self.order_id},{str(self.trove)},{self.filename},{self.remote_modified_date},"
                f"{self.local_modified_date},{self.md5}")

    def __iter__(self) -> Iterator[str]:
        return iter([str(self.order_id), self.filename, str(self.md5), str(self.remote_modified_date),
                     str(self.local_modified_date), str(self.trove)])

    def __eq__(self, other):
        if other is None:
            return False
        if not hasattr(other, "key"):
            return False
        return self.key == other.key

    def __contains__(self, item) -> bool:
        if any(item is c_attr or item == c_attr for c_attr in self.__dict__.keys()):
            return self[item] is not None
        return False

    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __mod__(self, other):
        """
        override modulus to give us a has compare, should be fun.
        :param other:
        :return:
        """
        if other is None:
            return False
        if not hasattr(other, "filename"):
            return False
        return self.filename == other.filename


class Cache(list):
    def __init__(self, cache_data: list[CsvCacheData]) -> None:
        super().__init__(cache_data)

    def __contains__(self, item):
        return any(item is c_data or item == c_data for c_data in self)

    def get_cache_item(self, order_id: str, filename: str, trove: bool = False) -> CsvCacheData:
        """
        returns a CsvCacheData, returns the one from the cache, if it is in the cahce, otherwise returns new
        CsvCacheData. This function is not enough to see if something is in cache, see is_cached(CsvCacheData)
        :param order_id: the order id for the cache item from HumbleBundle
        :param filename: the filename for the cache_item from HumbleBundle
        :param trove: if in humble trove or not (idk what this is tbh)
        :return: CsvCacheData
        """
        search = CsvCacheData(order_id, filename, trove=trove)
        for cache_data in self:
            if search == cache_data:
                return cache_data
        return search
