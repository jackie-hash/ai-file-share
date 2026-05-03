"""认证工具"""
import hashlib
import hmac
import secrets
import os

# API Key 哈希盐值
_API_KEY_SALT = os.getenv("API_KEY_SALT", "file-share-cloud-v2").encode()


def generate_api_key() -> tuple:
    """生成新的 API Key

    Returns:
        (raw_key, key_hash, key_prefix)
    """
    raw_key = f"fsc_{secrets.token_urlsafe(24)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:12]
    return raw_key, key_hash, key_prefix


def hash_api_key(api_key: str) -> str:
    """对 API Key 进行加盐哈希（HMAC-SHA256）"""
    return hmac.new(_API_KEY_SALT, api_key.encode(), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    """对分享密码进行 PBKDF2-SHA256 哈希，格式: pbkdf2:sha256:iterations:salt:hash"""
    iterations = 100000
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"pbkdf2:sha256:{iterations}:{salt}:{dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """验证密码。兼容旧版明文密码（向后兼容）。"""
    if not stored:
        return False
    if not stored.startswith("pbkdf2:"):
        # 旧版明文密码，直接比较
        return hmac.compare_digest(password.encode(), stored.encode())
    # 新版 PBKDF2 哈希
    parts = stored.split(":")
    if len(parts) != 5:
        return False
    _, algorithm, iterations, salt, stored_hash = parts
    dk = hashlib.pbkdf2_hmac(algorithm, password.encode(), salt.encode(), int(iterations))
    return hmac.compare_digest(dk.hex().encode(), stored_hash.encode())
