import os
import struct
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pass_key import PASS


def decrypt(encrypted_path, private_key_path, password, output_path):
    """Упрощенная версия дешифрования"""
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


def process_file(input_path):
    if not os.path.isfile(input_path):
        print(f"[PASSED] {os.path.basename(input_path)} is not a file!")
        return
    base, ext = os.path.splitext(input_path)
    if ext != ".enc":
        print(f"[PASSED] {os.path.basename(input_path)} is a not .enc file!")
        return
    if os.path.getsize(input_path) < 1024:
        print(f"[PASSED] {os.path.basename(input_path)} is a low size file ({os.path.getsize(input_path)})!")
        return
    output_path = base + ".dec.mp4"
    if os.path.exists(output_path):
        print(f"[SKIPPED] {os.path.basename(input_path)} already has decoded version!")
        return
    decrypt(input_path, "private_key.pem", PASS, output_path)
    print(f"[OK] {os.path.basename(input_path)} → {os.path.basename(output_path)}")


def process_dir(input_path):
    """Обработка всех .enc файлов в директории и поддиректориях"""
    if not os.path.isdir(input_path):
        print(f"[ERROR] {input_path} is not a directory!")
        return

    print(f"[INFO] Scanning directory: {input_path}")

    # Используем glob для поиска всех .enc файлов
    enc_files = list(Path(input_path).rglob("*.enc"))

    if not enc_files:
        print(f"[INFO] No .enc files found in {input_path}")
        return

    print(f"[INFO] Found {len(enc_files)} .enc file(s)")

    for enc_file in enc_files:
        enc_file_path = str(enc_file)
        print(f"\n[PROCESSING] {enc_file.relative_to(input_path)}")
        process_file(enc_file_path)

    print(f"\n[COMPLETE] Processed {len(enc_files)} file(s)")


def main(input_path):
    if os.path.isfile(input_path):
        process_file(input_path)
    elif os.path.isdir(input_path):
        process_dir(input_path)
    else:
        print(f"[ERROR] '{input_path}' is not a file or directory.")
        sys.exit(1)


if __name__ == "__main__":
    main(r"C:\Users\UserLog.ru\PycharmProjects\up_server\crypt")
