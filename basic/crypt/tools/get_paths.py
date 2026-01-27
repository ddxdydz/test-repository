import os
from pathlib import Path

from .print_message import *


def get_file_output_path(input_path, input_file_extension, output_file_extension) -> str:
    if not os.path.isfile(input_path):
        print_message(f"{os.path.basename(input_path)} is not a file!", PASSED)
        return ''
    base, ext = os.path.splitext(input_path)
    if ext != input_file_extension:
        print_message(f"{os.path.basename(input_path)} is a not {input_file_extension} file!", PASSED)
        return ''
    if os.path.getsize(input_path) < 1024:
        print_message(f"{os.path.basename(input_path)} is a low size file ({os.path.getsize(input_path)})!", PASSED)
        return ''
    output_path = base + output_file_extension
    if os.path.exists(output_path):
        print_message(f"{os.path.basename(input_path)} already has {output_file_extension} version!", PASSED)
        return ''
    return output_path


def get_paths(input_path, input_file_extension, output_file_extension) -> list[tuple]:
    if len(input_file_extension) < 2 or input_file_extension[0] != '.':
        print_error_and_exit(f"Bad input_file_extension: {input_file_extension}.")

    if len(output_file_extension) < 2 or output_file_extension[0] != '.':
        print_error_and_exit(f"Bad output_file_extension: {output_file_extension}.")

    if os.path.isfile(input_path):
        output_path = get_file_output_path(input_path, input_file_extension, output_file_extension)
        if not output_path:
            print_error_and_exit(f"{input_path} is bad.")
        return [(input_path, output_path)]

    if not os.path.isdir(input_path):
        print_error_and_exit(f"{input_path} is not a directory or file!")

    print_message(f"Scanning directory ({input_path})...")
    founded_files = list(Path(input_path).rglob(f"*{input_file_extension}"))

    if not founded_files:
        print_message(f"No {input_file_extension} files found in {input_path}")
        return []

    print_message(f"Found {len(founded_files)} .enc file(s)")

    output_paths = []
    for founded_file in founded_files:
        output_path = get_file_output_path(str(founded_file), input_file_extension, output_file_extension)
        if output_path:
            output_paths.append((str(founded_file), output_path))

    return output_paths
