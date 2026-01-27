import os
import struct
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from key.pass_key import PASS
from tools.get_paths import get_paths
from tools.print_message import print_message, SUCCESS, OK, PROCESSING


def decrypt(encrypted_path, private_key_path, password, output_path):
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=password.encode() if isinstance(password, str) else password,
        )

    with open(encrypted_path, "rb") as f_in, open(output_path, "wb") as f_out:
        key_len = struct.unpack("<I", f_in.read(4))[0]
        encrypted_aes_key = f_in.read(key_len)
        iv = f_in.read(16)

        encrypted_data = f_in.read()
        tag = encrypted_data[-16:]
        ciphertext = encrypted_data[:-16]

        aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()

        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        f_out.write(plaintext)


def main(process_path=None):
    if process_path is None:
        process_path = sys.argv[1]
    private_key = Path(__file__).parent / "key" / "private_key.pem"
    paths = get_paths(process_path, '.enc', '.dec.mp4')
    if not paths:
        return
    for input_path, output_path in paths:
        print_message(f"{input_path}", PROCESSING)
        decrypt(input_path, private_key, PASS, output_path)
        print_message(f"{os.path.basename(input_path)} → {os.path.basename(output_path)}", OK)
    print_message(f"{len(paths)} files are processed!", SUCCESS)


if __name__ == "__main__":
    main(r".\test_data")
    # main(r"C:\Users\UserLog.ru\Downloads\archive")
    # main()
