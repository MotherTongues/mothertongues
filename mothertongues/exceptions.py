class ParserError(Exception):
    def __init__(self, msg):
        super().__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class ConfigurationError(Exception):
    def __init__(self, msg):
        super().__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class UnsupportedFiletypeError(Exception):
    """Raise when unable to import parser for filetype"""

    def __init__(self, path, msg=""):
        self.path = path
        self.msg = msg

    def __str__(self):
        if self.msg:
            return self.msg

        return f"Filetype at {self.path} is unsupported."
