class IsNegativeError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)


class IsNotCrafter(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)


class IsNotMention(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)


class NotEnoughtPoints(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)
