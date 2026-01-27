from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pass_key import PASS

# Генерация пары ключей (2048 бит)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Сохранение закрытого ключа (защищаем паролем)
pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(PASS)
)
with open("private_key.pem", "wb") as f:
    f.write(pem_private)

# Сохранение открытого ключа
pem_public = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
with open("public_key.pem", "wb") as f:
    f.write(pem_public)
