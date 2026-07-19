"""
Cifrado en reposo del secreto TOTP (2FA).

Mismo problema y misma solución que modules/integration_service/token_crypto.py
(tokens OAuth): un secreto TOTP en texto plano en la tabla `users` da acceso
indefinido a generar códigos válidos si la base de datos se filtra. Se cifra
con Fernet (AES-128-CBC + HMAC), self-contained en este módulo en vez de
importar el helper privado de token_crypto.py — mismo criterio de aislamiento
que ya usa el resto del proyecto entre módulos de auth independientes.

Clave: TOKEN_ENCRYPTION_KEY (la misma variable que usa token_crypto.py — un
solo secreto de cifrado para todo lo que la app cifra en reposo). Si no está,
se deriva de forma estable desde SECRET_KEY.
"""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is not None:
        return _fernet

    key = os.environ.get("TOKEN_ENCRYPTION_KEY", "").strip()
    if key:
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
        return _fernet

    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY o SECRET_KEY deben estar configurados para "
            "cifrar el secreto TOTP."
        )
    derived = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    _fernet = Fernet(derived)
    return _fernet


def encrypt_secret(plaintext: str) -> str:
    """Cifra el secreto base32 de TOTP. Devuelve texto Fernet (str)."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(stored: str) -> str | None:
    """Descifra el secreto TOTP. None si el valor es inválido/corrupto —
    nunca se asume texto plano heredado (a diferencia de token_crypto.py,
    aquí no existían filas pre-cifrado: la columna se estrena ya cifrada)."""
    if not stored:
        return None
    try:
        return _get_fernet().decrypt(stored.encode()).decode()
    except (InvalidToken, ValueError):
        return None
