import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

SALT = "thpay_secure_salt_2026"
SESSION_DURATION_HOURS = 24

def hash_password(password: str) -> str:
    return hashlib.sha256(f"{SALT}{password}".encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed: str) -> bool:
    return hash_password(plain_password) == hashed

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

class AuthService:
    @staticmethod
    def authenticate(
        db,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Tuple[Dict[str, Any], str]]:
        user = db.fetchone(
            "SELECT * FROM users WHERE email = ? AND is_active = 1;",
            (email.strip().lower(),)
        )
        if not user:
            return None
            
        if not verify_password(password, user["password_hash"]):
            return None
            
        # Gerar token opaco seguro de sessao
        raw_token = secrets.token_urlsafe(32)
        token_hashed = hash_token(raw_token)
        session_id = f"sess-{secrets.token_hex(16)}"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=SESSION_DURATION_HOURS)
        
        db.execute("""
            INSERT INTO sessions (id, user_id, token_hash, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (session_id, user["id"], token_hashed, expires_at.isoformat(), ip_address, user_agent))
        
        db.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?;",
            (user["id"],)
        )
        
        # Buscar permissoes do perfil
        perms = db.fetchall(
            "SELECT permission_code FROM role_permissions WHERE role_code = ?;",
            (user["role"],)
        )
        user_dict = dict(user)
        user_dict.pop("password_hash", None)
        user_dict["permissions"] = [p["permission_code"] for p in perms]
        
        return user_dict, raw_token

    @staticmethod
    def verify_token(db, raw_token: str) -> Optional[Dict[str, Any]]:
        token_hashed = hash_token(raw_token)
        now_str = datetime.now(timezone.utc).isoformat()
        
        session = db.fetchone(
            "SELECT * FROM sessions WHERE token_hash = ? AND expires_at > ?;",
            (token_hashed, now_str)
        )
        if not session:
            return None
            
        user = db.fetchone(
            "SELECT * FROM users WHERE id = ? AND is_active = 1;",
            (session["user_id"],)
        )
        if not user:
            return None
            
        perms = db.fetchall(
            "SELECT permission_code FROM role_permissions WHERE role_code = ?;",
            (user["role"],)
        )
        user_dict = dict(user)
        user_dict.pop("password_hash", None)
        user_dict["permissions"] = [p["permission_code"] for p in perms]
        user_dict["session_id"] = session["id"]
        return user_dict

    @staticmethod
    def logout(db, raw_token: str) -> bool:
        token_hashed = hash_token(raw_token)
        cursor = db.execute("DELETE FROM sessions WHERE token_hash = ?;", (token_hashed,))
        return True
