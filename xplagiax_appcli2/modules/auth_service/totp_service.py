"""
Lógica de Two-Factor Authentication (TOTP — Google Authenticator / Authy).

Todo lo que sabe de pyotp/qrcode/bcrypt vive aquí; auth_routes_fixed.py solo
orquesta HTTP (parseo de request, respuesta JSON, current_user). Mantiene el
mismo reparto de responsabilidades que el resto del proyecto (p.ej.
DOIResolver/CitationValidator en finderx: la ruta es una cáscara delgada).
"""

from __future__ import annotations

import base64
import io
import json
import secrets

import bcrypt
import pyotp
import qrcode

_ISSUER = "XplagiaX"
_RECOVERY_CODE_COUNT = 10


def generate_secret() -> str:
    """Secreto base32 de 160 bits — el mínimo que pyotp acepta sin advertencia."""
    return pyotp.random_base32()


def provisioning_qr_data_uri(secret: str, email: str) -> str:
    """QR listo para <img src="..."> — data URI PNG, sin necesidad de una
    ruta/archivo estático adicional."""
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=_ISSUER)
    img = qrcode.make(uri, box_size=6, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def verify_totp_code(secret: str, code: str) -> bool:
    """valid_window=1 tolera ±30s de desfase de reloj entre el teléfono y el
    servidor — sin esto, códigos legítimos fallan por drift normal de reloj."""
    code = (code or "").strip().replace(" ", "")
    if not code.isdigit():
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_recovery_codes() -> tuple[list[str], str]:
    """Genera N códigos de un solo uso (formato xxxx-xxxx) para cuando el
    usuario pierde el dispositivo con la app autenticadora.

    Devuelve (códigos en texto plano — mostrar UNA vez, nunca recuperables
    después, list[str]), y su representación hasheada+serializada lista para
    guardar en Users.totp_recovery_codes (str, JSON de hashes bcrypt).
    """
    plain_codes = []
    hashed_codes = []
    for _ in range(_RECOVERY_CODE_COUNT):
        raw = secrets.token_hex(4)  # 8 hex chars
        formatted = f"{raw[:4]}-{raw[4:]}"
        plain_codes.append(formatted)
        hashed = bcrypt.hashpw(formatted.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        hashed_codes.append(hashed)
    return plain_codes, json.dumps(hashed_codes)


def consume_recovery_code(stored_json: str | None, code: str) -> str | None:
    """Si `code` coincide con alguno de los hashes guardados, lo consume
    (elimina de la lista) y devuelve el JSON actualizado para persistir.
    Devuelve None si no hubo match (nada que guardar, código rechazado)."""
    if not stored_json or not code:
        return None
    try:
        hashes = json.loads(stored_json)
    except (ValueError, TypeError):
        return None

    code_bytes = code.strip().encode("utf-8")
    for i, h in enumerate(hashes):
        try:
            if bcrypt.checkpw(code_bytes, h.encode("utf-8")):
                remaining = hashes[:i] + hashes[i + 1:]
                return json.dumps(remaining)
        except ValueError:
            continue
    return None
