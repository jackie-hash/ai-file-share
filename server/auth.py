"""认证工具"""
import hashlib
import secrets


def generate_api_key() -> tuple:
    """生成新的 API Key

    Returns:
        (raw_key, key_hash, key_prefix)
    """
    raw_key = f"fsc_{secrets.token_urlsafe(24)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:12]  # 用于显示的前缀
    return raw_key, key_hash, key_prefix


def hash_api_key(api_key: str) -> str:
    """对 API Key 进行哈希"""
    return hashlib.sha256(api_key.encode()).hexdigest()
