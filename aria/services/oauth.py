# filename: services/oauth.py
# purpose: Provider-agnostic OAuth 2.0 connect/callback/refresh with Redis state and encrypted credential persistence.
# dependencies: os, hashlib, urllib.parse, httpx, asyncpg, redis.asyncio, cryptography.fernet

from __future__ import annotations

import hashlib
import os
from urllib.parse import urlencode

import asyncpg
import httpx
import redis.asyncio as redis
from cryptography.fernet import Fernet

from db.connection import set_tenant


SERVICE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"


class OAuthService:
    def __init__(self, pool: asyncpg.Pool, redis_client: redis.Redis) -> None:
        self.pool = pool
        self.redis = redis_client
        key = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "").strip()
        if not key or key == "replace-me":
            key = Fernet.generate_key().decode("utf-8")
        try:
            self.fernet = Fernet(key.encode("utf-8"))
        except Exception as exc:  # pragma: no cover - defensive config validation
            raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY must be a valid Fernet key") from exc
        self.secret = os.getenv("OAUTH_STATE_SECRET", "aria-state-secret")
        self.redirect_base = os.getenv("OAUTH_CALLBACK_BASE_URL", "http://localhost:8000")

    def _cfg(self, platform: str) -> dict[str, str]:
        p = platform.upper()
        return {
            "client_id": os.getenv(f"{p}_CLIENT_ID", ""),
            "client_secret": os.getenv(f"{p}_CLIENT_SECRET", ""),
            "auth_url": os.getenv(f"{p}_AUTH_URL", ""),
            "token_url": os.getenv(f"{p}_TOKEN_URL", ""),
            "scopes": os.getenv(f"{p}_SCOPES", ""),
        }

    async def get_authorization_url(self, company_id: str, platform: str) -> str:
        cfg = self._cfg(platform)
        if not cfg["client_id"] or not cfg["auth_url"]:
            raise ValueError(f"OAuth config missing for platform {platform}")

        raw = f"{company_id}{platform}{self.secret}"
        state = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        await self.redis.set(f"oauth:state:{state}", f"{company_id}:{platform}", ex=600)

        redirect_uri = f"{self.redirect_base}/v1/oauth/callback"
        query = urlencode(
            {
                "response_type": "code",
                "client_id": cfg["client_id"],
                "redirect_uri": redirect_uri,
                "scope": cfg["scopes"],
                "state": state,
            }
        )
        return f"{cfg['auth_url']}?{query}"

    async def handle_callback(self, code: str, state: str, platform: str) -> dict[str, str]:
        state_key = f"oauth:state:{state}"
        state_val = await self.redis.get(state_key)
        if state_val is None:
            raise ValueError("Invalid or expired OAuth state")

        company_id, state_platform = state_val.split(":", 1)
        if state_platform.lower() != platform.lower():
            raise ValueError("OAuth state platform mismatch")

        cfg = self._cfg(platform)
        redirect_uri = f"{self.redirect_base}/v1/oauth/callback"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_resp = await client.post(cfg["token_url"], data=payload)
        if token_resp.status_code >= 400:
            raise ValueError(f"OAuth token exchange failed: {token_resp.status_code} {token_resp.text}")

        token_data = token_resp.json()
        access_token = str(token_data.get("access_token", ""))
        refresh_token = str(token_data.get("refresh_token", ""))
        expires_in = int(token_data.get("expires_in", 3600))

        enc_access = self.fernet.encrypt(access_token.encode("utf-8")).decode("utf-8")
        enc_refresh = self.fernet.encrypt(refresh_token.encode("utf-8")).decode("utf-8") if refresh_token else None

        scopes = [s.strip() for s in cfg["scopes"].split(",") if s.strip()]
        query = """
        INSERT INTO platform_credentials (
            company_id, platform, account_ref,
            access_token_encrypted, refresh_token_encrypted,
            token_expires_at, scopes, status
        ) VALUES (
            $1::uuid, $2, $3,
            $4, $5,
            now() + ($6 || ' seconds')::interval,
            $7::text[], 'active'
        )
        ON CONFLICT (company_id, platform, account_ref)
        DO UPDATE SET
            access_token_encrypted = EXCLUDED.access_token_encrypted,
            refresh_token_encrypted = EXCLUDED.refresh_token_encrypted,
            token_expires_at = EXCLUDED.token_expires_at,
            scopes = EXCLUDED.scopes,
            status = 'active',
            last_refresh_at = now()
        RETURNING credential_id, platform, status
        """

        account_ref = str(token_data.get("account_id") or token_data.get("user_id") or f"acct-{platform}-{company_id}")
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                row = await conn.fetchrow(
                    query,
                    company_id,
                    platform,
                    account_ref,
                    enc_access,
                    enc_refresh,
                    expires_in,
                    scopes,
                )

        await self.redis.delete(state_key)
        return {
            "credential_id": str(row["credential_id"]),
            "platform": str(row["platform"]),
            "status": str(row["status"]),
        }

    async def refresh_token(self, credential_id: str) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
                row = await conn.fetchrow(
                    """
                    SELECT credential_id, platform, company_id, account_ref, refresh_token_encrypted
                    FROM platform_credentials
                    WHERE credential_id = $1::uuid
                    """,
                    credential_id,
                )
                if row is None:
                    raise ValueError("Credential not found")

                platform = str(row["platform"])
                company_id = str(row["company_id"])
                cfg = self._cfg(platform)
                enc_refresh = row["refresh_token_encrypted"]
                if not enc_refresh:
                    raise ValueError("No refresh token available")
                refresh_token = self.fernet.decrypt(str(enc_refresh).encode("utf-8")).decode("utf-8")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            token_resp = await client.post(cfg["token_url"], data=payload)
        if token_resp.status_code >= 400:
            raise ValueError(f"OAuth token refresh failed: {token_resp.status_code} {token_resp.text}")

        token_data = token_resp.json()
        access_token = str(token_data.get("access_token", ""))
        new_refresh_token = str(token_data.get("refresh_token", refresh_token))
        expires_in = int(token_data.get("expires_in", 3600))

        enc_access = self.fernet.encrypt(access_token.encode("utf-8")).decode("utf-8")
        enc_refresh = self.fernet.encrypt(new_refresh_token.encode("utf-8")).decode("utf-8")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                await conn.execute(
                    """
                    UPDATE platform_credentials
                    SET access_token_encrypted = $2,
                        refresh_token_encrypted = $3,
                        token_expires_at = now() + ($4 || ' seconds')::interval,
                        last_refresh_at = now(),
                        status = 'active'
                    WHERE credential_id = $1::uuid
                    """,
                    credential_id,
                    enc_access,
                    enc_refresh,
                    expires_in,
                )
