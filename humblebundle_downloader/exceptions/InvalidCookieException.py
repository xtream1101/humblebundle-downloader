class InvalidCookieException(Exception):
    def __init__(self):
        super().__init__("Unable to download user-data, cookies missing?")