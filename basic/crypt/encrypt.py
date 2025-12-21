import os
import struct
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

EXT = ".mp4"


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

        while True:
            chunk = f_in.read(65536)
            if not chunk:
                break
            ciphertext = encryptor.update(chunk)
            f_out.write(ciphertext)

        ciphertext = encryptor.finalize()
        f_out.write(ciphertext)
        f_out.write(encryptor.tag)


def process_file(input_path):
    if not os.path.isfile(input_path):
        print(f"[PASSED] {os.path.basename(input_path)} is not a file!")
        return
    base, ext = os.path.splitext(input_path)
    if ext != EXT:
        print(f"[PASSED] {os.path.basename(input_path)} is a not {EXT} file!")
        return
    if os.path.getsize(input_path) < 1024:
        print(f"[PASSED] {os.path.basename(input_path)} is a low size file ({os.path.getsize(input_path)})!")
        return
    output_path = base + ".enc"
    if os.path.exists(output_path):
        print(f"[SKIPPED] {os.path.basename(input_path)} already has encoded version!")
        return
    encrypt(input_path, "./public_key.pem", output_path)
    print(f"[OK] {os.path.basename(input_path)} → {os.path.basename(output_path)}")


def process_dir(input_path):
    if not os.path.isdir(input_path):
        print(f"[ERROR] {input_path} is not a directory!")
        return

    print(f"[INFO] Scanning directory: {input_path}")

    enc_files = list(Path(input_path).rglob(f"*{EXT}"))

    if not enc_files:
        print(f"[INFO] No {EXT} files found in {input_path}")
        return

    print(f"[INFO] Found {len(enc_files)} .enc file(s)")

    for enc_file in enc_files:
        enc_file_path = str(enc_file)
        print(f"\n[PROCESSING] {enc_file.relative_to(input_path)}")
        process_file(enc_file_path)

    print(f"\n[COMPLETE] Processed {len(enc_files)} file(s)")


def main(input_path=None):
    if input_path is None:
        input_path = sys.argv[1]
    if os.path.isfile(input_path):
        process_file(input_path)
    elif os.path.isdir(input_path):
        process_dir(input_path)
    else:
        print(f"[ERROR] '{input_path}' is not a file or directory.")
        sys.exit(1)


if __name__ == "__main__":
    # main(r".\test_data")
    main()
