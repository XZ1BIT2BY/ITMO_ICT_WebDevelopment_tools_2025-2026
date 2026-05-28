import hashlib
import os
import hmac


def hash_password(plain_password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations=260_000,
    )
    return salt.hex() + ":" + key.hex()


def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        salt_hex, key_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        stored_key = bytes.fromhex(key_hex)
    except ValueError:
        return False

    new_key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations=260_000,
    )
    return hmac.compare_digest(stored_key, new_key)