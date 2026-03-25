import os
import struct
import sys
from math import ceil
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from tools.get_paths import get_paths
from tools.print_message import print_message, SUCCESS, OK, PROCESSING

PROGRESS_INDICATOR_STEP = 10


def encrypt(file_path, public_key_path, output_path):
    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    aes_key = os.urandom(32)
    iv = os.urandom(16)

    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv))
    encryptor = cipher.encryptor()

    with open(file_path, "rb") as f_in, open(output_path, "wb") as f_out:
        f_out.write(struct.pack("<I", len(encrypted_aes_key)))
        f_out.write(encrypted_aes_key)
        f_out.write(iv)

        input_size = os.path.getsize(file_path)
        chunk_size = 65536
        size = 0

        is_print = [False] * (100 // PROGRESS_INDICATOR_STEP + 2)

        while True:
            chunk = f_in.read(chunk_size)
            if not chunk:
                break
            ciphertext = encryptor.update(chunk)
            f_out.write(ciphertext)

            size += chunk_size
            percent = int(size * 100 / input_size)
            progress_value = percent // PROGRESS_INDICATOR_STEP
            if not is_print[progress_value]:
                is_print[progress_value] = True
                print(f"{percent}%")
        if not is_print[ceil(100 / PROGRESS_INDICATOR_STEP)]:
            print("100%")

        ciphertext = encryptor.finalize()
        f_out.write(ciphertext)
        f_out.write(encryptor.tag)


def main(process_path=None):
    if process_path is None:
        process_path = sys.argv[1]
    public_key_path = Path(__file__).parent / "key" / "public_key.pem"
    paths = get_paths(process_path, '.mp4', '.enc')
    if not paths:
        return
    for input_path, output_path in paths:
        print_message(f"{input_path}", PROCESSING)
        encrypt(input_path, public_key_path, output_path)
        print_message(f"{os.path.basename(input_path)} → {os.path.basename(output_path)}", OK)
    print_message(f"{len(paths)} files are processed!", SUCCESS)


if __name__ == "__main__":
    main(r".\test_data")
    # main()
