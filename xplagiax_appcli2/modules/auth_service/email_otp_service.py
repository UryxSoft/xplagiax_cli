"""
Lógica de Two-Factor Authentication por email — segundo método, independiente
de TOTP (ver totp_service.py). El código nunca se guarda en texto plano: solo
su hash bcrypt + expiración en Users.email_otp_code_hash/email_otp_expires_at.
auth_routes_fixed.py orquesta HTTP y el envío del correo; este módulo solo
sabe de generación/hash/verificación del código — mismo reparto de
responsabilidades que totp_service.py.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

import bcrypt

_CODE_DIGITS = 4
_CODE_TTL_MINUTES = 10


def generate_code() -> str:
    """Código numérico de 4 dígitos. Generado con `secrets` (no `random`) por
    higiene criptográfica, aunque la defensa real contra fuerza bruta es el
    rate-limit de los endpoints /2fa/email/* — el espacio de 10,000 valores
    posibles es chico a propósito (4 dígitos, fácil de teclear desde el
    correo), igual que otros productos que usan OTP corto por email."""
    return f"{secrets.randbelow(10 ** _CODE_DIGITS):0{_CODE_DIGITS}d}"


def hash_code(code: str) -> str:
    return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def new_expiry() -> datetime:
    return datetime.utcnow() + timedelta(minutes=_CODE_TTL_MINUTES)


def verify_code(code: str, stored_hash: str | None, expires_at: datetime | None) -> bool:
    """True solo si el código coincide Y no venció. No consume/limpia nada
    por sí mismo — el caller es responsable de borrar
    email_otp_code_hash/email_otp_expires_at tras un match exitoso, para que
    cada código sirva una sola vez (mismo contrato que consume_recovery_code
    en totp_service.py, salvo que aquí el estado es un solo hash, no una
    lista)."""
    if not stored_hash or not expires_at or not code:
        return False
    if datetime.utcnow() > expires_at:
        return False
    try:
        return bcrypt.checkpw(code.strip().encode("utf-8"), stored_hash.encode("utf-8"))
    except ValueError:
        return False
