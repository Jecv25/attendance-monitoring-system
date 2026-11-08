import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

PASSWORDS = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
DUMMY_HASH = PASSWORDS.hash(secrets.token_urlsafe(24))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def verify_password(encoded: str, value: str) -> bool:
    try:
        return PASSWORDS.verify(encoded, value)
    except VerificationError:
        return False
