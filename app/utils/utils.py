from uuid import uuid4


def generate_random_string() -> str:
    return uuid4().hex
