class CustomException(Exception):
    detail = "Operation failed."
    errors = None
    status_code = 400

    def __init__(self, detail: str = None, errors: str = None, status_code: int = None):
        if detail:
            self.detail = detail
        if errors:
            self.errors = errors
        if status_code:
            self.status_code = status_code
