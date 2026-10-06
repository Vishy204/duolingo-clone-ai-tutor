class GameError(Exception):
    """A domain rule was violated (locked lesson, no hearts, ...). Mapped to an HTTP error by the API."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
