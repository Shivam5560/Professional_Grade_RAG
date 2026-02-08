"""Encryption utilities for AuraSQL secrets."""

from cryptography.fernet import Fernet
from app.config import settings


def get_fernet() -> Fernet:
    if not settings.aurasql_master_key:
        raise ValueError("AURASQL_MASTER_KEY is not configured")
    return Fernet(settings.aurasql_master_key.encode("utf-8"))


def encrypt_secret(value: str) -> str:
    fernet = get_fernet()
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    fernet = get_fernet()
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
