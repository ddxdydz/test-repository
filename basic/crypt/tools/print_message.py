import sys

INFO = "INFO"
ERROR = "ERROR"
OK = "OK"
PROCESSING = "PROCESSING"
PASSED = "PASSED"
SUCCESS = "SUCCESS"


def print_message(text="No text", message_type=INFO):
    print(f"[{message_type}] {text}")


def print_error_and_exit(text):
    print(f"[{ERROR}] {text}")
    sys.exit(1)
