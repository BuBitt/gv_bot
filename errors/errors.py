class IsNegativeError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)


class IsNotCrafterError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)


class IsNotMentionError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)


class NotEnoughtPointsError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)


class IsNotLinkError(Exception):
    def __init__(self, message=None):
        self.message = message
        super().__init__(message)
