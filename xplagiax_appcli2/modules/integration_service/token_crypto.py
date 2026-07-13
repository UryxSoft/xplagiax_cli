"""
Cifrado en reposo de los tokens OAuth de cloud storage (C-5).

Los tokens de acceso y refresh se guardaban en texto plano en la columna
Users.tokens. Un dump de la tabla, un backup o un acceso de soporte exponían
credenciales de larga vida. Este módulo los cifra con Fernet (AES-128-CBC +
HMAC) de forma TRANSPARENTE y RETROCOMPATIBLE:

  * encrypt_tokens(json_str)  → texto cifrado (Fernet).
  * decrypt_tokens(stored)    → intenta descifrar; si el valor es JSON en
    texto plano de una fila antigua (pre-cifrado), lo devuelve tal cual. La
    fila se re-cifra sola en el próximo save. Migración sin downtime.

Clave: variable de entorno TOKEN_ENCRYPTION_KEY (una Fernet key urlsafe-base64
de 32 bytes: `python -c "from cryptography.fernet import Fernet;
print(Fernet.generate_key().decode())"`). Si no está, se DERIVA de forma
estable desde SECRET_KEY (mejor que texto plano, pero se recomienda una clave
dedicada y rotable).
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

    # Fallback: derivar una Fernet key estable desde SECRET_KEY. No es ideal
    # (SECRET_KEY debería ser un secreto fuerte y separado) pero cifra en
    # reposo sin requerir configuración adicional para arrancar.
    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        raise RuntimeError(
            "TOKEN_ENCRYPTION_KEY o SECRET_KEY deben estar configurados para "
            "cifrar los tokens de cloud storage."
        )
    derived = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    _fernet = Fernet(derived)
    return _fernet


def encrypt_tokens(plaintext: str) -> str:
    """Cifra el JSON de tokens. Devuelve texto Fernet (str)."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_tokens(stored: str) -> str:
    """
    Descifra el JSON de tokens.

    Retrocompatible: si `stored` no es un token Fernet válido (fila antigua en
    texto plano), lo devuelve sin tocar para que json.loads lo lea igual. Se
    re-cifra en el próximo save_user_tokens.
    """
    if not stored:
        return stored
    try:
        return _get_fernet().decrypt(stored.encode()).decode()
    except (InvalidToken, ValueError):
        # Valor heredado en texto plano (JSON) — migración transparente.
        return stored
