"""
TokenRepository — capa de persistencia del ciclo de vida de los tokens OAuth
de cloud storage (Fase 3, patrón Repository).

Antes, el acceso a los tokens estaba disperso: cada ruta hacía
`json.loads(user.tokens)` / `json.dumps(...)` directo sobre el blob de la
columna Users.tokens, mezclando persistencia, serialización y cifrado en ~40
sitios. Esta clase encapsula todo eso detrás de una interfaz única:

    repo = TokenRepository(user_id)
    repo.all()                 # -> {provider: {...}}
    repo.get('dropbox')        # -> {...} | None
    repo.set('dropbox', {...}) # persiste un provider
    repo.remove('dropbox')     # desconecta un provider
    TokenRepository.is_expired(token_info)

El cifrado en reposo (token_crypto) y la comparación de expiración en UTC
viven aquí, en un solo lugar testeable. NO gestiona el intercambio HTTP de
tokens (eso es lógica OAuth del provider y permanece en las rutas).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import SQLAlchemyError

from modules.models.model import Users
from settings.connections import db
from modules.integration_service.token_crypto import decrypt_tokens, encrypt_tokens


class TokenRepository:
    """Persistencia por-usuario del mapa {provider: token_info}."""

    def __init__(self, user_id):
        self.user_id = user_id

    # ── Lectura ──────────────────────────────────────────────────────────────
    def all(self) -> dict:
        """Todos los tokens del usuario (descifrados). {} si no hay o falla."""
        try:
            user = db.session.query(Users).filter_by(id=self.user_id).first()
            if user and user.tokens:
                # decrypt_tokens es retrocompatible con filas antiguas en claro.
                return json.loads(decrypt_tokens(user.tokens))
            return {}
        except SQLAlchemyError as e:
            print(f"TokenRepository.all error: {e}")
            db.session.rollback()
            return {}

    def get(self, provider: str) -> dict | None:
        """token_info de un provider concreto, o None si no está conectado."""
        return self.all().get(provider)

    # ── Escritura ────────────────────────────────────────────────────────────
    def replace(self, tokens: dict) -> bool:
        """Reemplaza TODO el mapa de tokens (cifrado en reposo)."""
        try:
            user = db.session.query(Users).filter_by(id=self.user_id).first()
            if not user:
                print(f"TokenRepository.replace: usuario {self.user_id} no encontrado")
                return False
            user.tokens = encrypt_tokens(json.dumps(tokens))
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            print(f"TokenRepository.replace error: {e}")
            db.session.rollback()
            return False

    def set(self, provider: str, token_info: dict) -> bool:
        """Persiste (o actualiza) el token de UN provider sin tocar los demás."""
        tokens = self.all()
        tokens[provider] = token_info
        return self.replace(tokens)

    def remove(self, provider: str) -> bool:
        """Desconecta un provider. False si no estaba conectado."""
        tokens = self.all()
        if provider not in tokens:
            return False
        del tokens[provider]
        return self.replace(tokens)

    # ── Expiración ───────────────────────────────────────────────────────────
    @staticmethod
    def is_expired(token_info: dict) -> bool:
        """
        True si el access token está (o está a <60s de estar) vencido.

        A-4: comparación en UTC-aware; tolera timestamps antiguos naive
        (se asumen UTC). Margen de 60s para renovar antes de que falle.
        """
        if not token_info or 'expires_at' not in token_info:
            return False
        expires_at = datetime.fromisoformat(token_info['expires_at'])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= (expires_at - timedelta(seconds=60))
