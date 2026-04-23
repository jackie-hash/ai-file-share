"""数据库管理 - SQLite 存储"""
import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path
import json


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        """获取配置了 row_factory 的数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_row_dict(self, row) -> dict:
        """将 sqlite3.Row 转换为字典"""
        if row is None:
            return None
        return dict(zip(row.keys(), row))

    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Agent 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id TEXT PRIMARY KEY,
                    api_key_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    last_seen TEXT,
                    is_active INTEGER DEFAULT 1,
                    storage_used INTEGER DEFAULT 0,
                    storage_quota INTEGER DEFAULT 10737418240
                )
            """)  # 默认10GB配额

            # 文件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    content_type TEXT,
                    agent_id TEXT NOT NULL,
                    content_hash TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    tags TEXT,
                    description TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    FOREIGN KEY (agent_id) REFERENCES agents(id)
                )
            """)

            # 分享表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shares (
                    id TEXT PRIMARY KEY,
                    share_code TEXT NOT NULL UNIQUE,
                    file_id TEXT NOT NULL,
                    creator_agent_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    max_downloads INTEGER,
                    download_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    password_protected TEXT,
                    FOREIGN KEY (file_id) REFERENCES files(id)
                )
            """)

            # 下载记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    share_id TEXT,
                    file_id TEXT NOT NULL,
                    downloaded_by TEXT,
                    downloaded_at TEXT NOT NULL,
                    ip_address TEXT
                )
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_agent ON files(agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_shares_code ON shares(share_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_file ON downloads(file_id)")

            conn.commit()

    # ========== Agent 管理 ==========

    def create_agent(self, agent_id: str, api_key_hash: str) -> dict:
        """创建新 Agent"""
        now = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO agents (id, api_key_hash, created_at, is_active)
                   VALUES (?, ?, ?, 1)""",
                (agent_id, api_key_hash, now)
            )
            conn.commit()
            return {"id": agent_id, "created_at": now}

    def get_agent_by_key_hash(self, api_key_hash: str) -> Optional[dict]:
        """通过 Key Hash 获取 Agent"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agents WHERE api_key_hash = ? AND is_active = 1",
                (api_key_hash,)
            )
            row = cursor.fetchone()
            return self._get_row_dict(row) if row else None

    def update_agent_last_seen(self, agent_id: str):
        """更新 Agent 最后访问时间"""
        now = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE agents SET last_seen = ? WHERE id = ?", (now, agent_id))
            conn.commit()

    def list_agents(self) -> List[dict]:
        """列出所有 Agent"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._get_row_dict(row) for row in rows]

    def update_agent_storage(self, agent_id: str, delta_size: int):
        """更新 Agent 存储使用量"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE agents SET storage_used = storage_used + ? WHERE id = ?",
                (delta_size, agent_id)
            )
            conn.commit()

    def get_agent_storage(self, agent_id: str) -> dict:
        """获取 Agent 存储信息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT storage_used, storage_quota FROM agents WHERE id = ?",
                (agent_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {"storage_used": 0, "storage_quota": 10737418240}

    # ========== 文件管理 ==========

    def create_file(self, file_id: str, filename: str, original_filename: str,
                    file_path: str, file_size: int, content_type: str,
                    agent_id: str, content_hash: str = None,
                    tags: List[str] = None) -> dict:
        """创建文件记录"""
        now = datetime.utcnow().isoformat()
        tags_json = json.dumps(tags) if tags else None

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO files (id, filename, original_filename, file_path, file_size,
                                   content_type, agent_id, content_hash, created_at, updated_at, tags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_id, filename, original_filename, file_path, file_size,
                 content_type, agent_id, content_hash, now, now, tags_json)
            )
            conn.commit()

            # 更新存储使用量
            self.update_agent_storage(agent_id, file_size)

            return {"id": file_id, "filename": original_filename, "created_at": now}

    def get_file_by_id(self, file_id: str) -> Optional[dict]:
        """通过ID获取文件"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE id = ? AND is_deleted = 0", (file_id,))
            row = cursor.fetchone()
            return self._get_row_dict(row) if row else None

    def get_file_by_hash(self, content_hash: str, agent_id: str) -> Optional[dict]:
        """通过内容哈希检查是否已存在（去重）"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM files WHERE content_hash = ? AND agent_id = ? AND is_deleted = 0",
                (content_hash, agent_id)
            )
            row = cursor.fetchone()
            return self._get_row_dict(row) if row else None

    def list_files(self, agent_id: str, limit: int = 100, offset: int = 0) -> List[dict]:
        """列出 Agent 的文件"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, filename, original_filename, file_size, content_type,
                          agent_id, created_at, tags FROM files
                   WHERE agent_id = ? AND is_deleted = 0
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (agent_id, limit, offset)
            )
            rows = cursor.fetchall()
            return [self._get_row_dict(row) for row in rows]

    def count_files(self, agent_id: str) -> int:
        """统计文件数量"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM files WHERE agent_id = ? AND is_deleted = 0",
                (agent_id,)
            )
            return cursor.fetchone()[0]

    def search_files(self, agent_id: str, query: str) -> List[dict]:
        """搜索文件"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, filename, original_filename, file_size, content_type,
                          agent_id, created_at, tags FROM files
                   WHERE agent_id = ? AND is_deleted = 0
                   AND (original_filename LIKE ? OR tags LIKE ? OR description LIKE ?)
                   ORDER BY created_at DESC""",
                (agent_id, f"%{query}%", f"%{query}%", f"%{query}%")
            )
            rows = cursor.fetchall()
            return [self._get_row_dict(row) for row in rows]

    def update_file_tags(self, file_id: str, tags: List[str]):
        """更新文件标签"""
        tags_json = json.dumps(tags)
        now = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE files SET tags = ?, updated_at = ? WHERE id = ?",
                (tags_json, now, file_id)
            )
            conn.commit()

    def delete_file(self, file_id: str, agent_id: str) -> bool:
        """删除文件（软删除）"""
        file_info = self.get_file_by_id(file_id)
        if not file_info or file_info["agent_id"] != agent_id:
            return False

        now = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE files SET is_deleted = 1, updated_at = ? WHERE id = ?",
                (now, file_id)
            )
            conn.commit()

        # 更新存储使用量
        self.update_agent_storage(agent_id, -file_info["file_size"])
        return True

    def get_file_stats(self, agent_id: str) -> dict:
        """获取 Agent 的文件统计"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT COUNT(*) as count, COALESCE(SUM(file_size), 0) as total_size
                   FROM files WHERE agent_id = ? AND is_deleted = 0""",
                (agent_id,)
            )
            row = cursor.fetchone()
            return {"file_count": row[0], "total_size": row[1]}

    # ========== 分享管理 ==========

    def create_share(self, file_id: str, creator_agent_id: str,
                     expires_hours: int = 24, max_downloads: int = None,
                     password: str = None) -> dict:
        """创建分享链接"""
        share_id = secrets.token_hex(8)
        share_code = secrets.token_urlsafe(6)[:8]  # 8位简短分享码

        now = datetime.utcnow()
        expires_at = (now + timedelta(hours=expires_hours)).isoformat() if expires_hours else None
        created_at = now.isoformat()

        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO shares (id, share_code, file_id, creator_agent_id, created_at,
                                   expires_at, max_downloads, password_protected)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (share_id, share_code, file_id, creator_agent_id, created_at,
                 expires_at, max_downloads, password)
            )
            conn.commit()

        return {
            "id": share_id,
            "share_code": share_code,
            "created_at": created_at,
            "expires_at": expires_at
        }

    def get_share_by_code(self, share_code: str) -> Optional[dict]:
        """通过分享码获取分享信息"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT s.*, f.filename, f.file_size, f.file_path, f.content_type
                   FROM shares s JOIN files f ON s.file_id = f.id
                   WHERE s.share_code = ? AND s.is_active = 1 AND f.is_deleted = 0""",
                (share_code,)
            )
            row = cursor.fetchone()
            return self._get_row_dict(row) if row else None

    def validate_share(self, share_code: str, password: str = None) -> tuple:
        """验证分享是否有效，返回 (valid, error_message, file_info)"""
        share = self.get_share_by_code(share_code)

        if not share:
            return False, "分享不存在或已失效", None

        if not share.get("is_active"):
            return False, "分享已禁用", None

        # 检查过期
        if share.get("expires_at"):
            expires_at = datetime.fromisoformat(share["expires_at"])
            if datetime.utcnow() > expires_at:
                return False, "分享已过期", None

        # 检查下载次数
        if share.get("max_downloads") and share["download_count"] >= share["max_downloads"]:
            return False, "下载次数已用完", None

        # 检查密码
        if share.get("password_protected"):
            if not password or password != share["password_protected"]:
                return False, "需要密码访问", None

        return True, None, share

    def increment_download_count(self, share_id: str):
        """增加下载次数"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE shares SET download_count = download_count + 1 WHERE id = ?",
                (share_id,)
            )
            conn.commit()

    def log_download(self, share_id: str, file_id: str, downloaded_by: str = None, ip: str = None):
        """记录下载"""
        now = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO downloads (share_id, file_id, downloaded_by, downloaded_at, ip_address) VALUES (?, ?, ?, ?, ?)",
                (share_id, file_id, downloaded_by, now, ip)
            )
            conn.commit()

    def list_shares(self, agent_id: str) -> List[dict]:
        """列出 Agent 的所有分享"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT s.*, f.original_filename as filename
                   FROM shares s JOIN files f ON s.file_id = f.id
                   WHERE s.creator_agent_id = ? AND s.is_active = 1
                   ORDER BY s.created_at DESC""",
                (agent_id,)
            )
            rows = cursor.fetchall()
            return [self._get_row_dict(row) for row in rows]

    def deactivate_share(self, share_id: str, agent_id: str) -> bool:
        """禁用分享"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE shares SET is_active = 0 WHERE id = ? AND creator_agent_id = ?",
                (share_id, agent_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_file_shares(self, file_id: str) -> List[dict]:
        """获取文件的所有分享"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM shares WHERE file_id = ? AND is_active = 1""",
                (file_id,)
            )
            rows = cursor.fetchall()
            return [self._get_row_dict(row) for row in rows]


# 全局数据库实例
db = Database(os.getenv("DB_PATH", "/data/db/file_share.db"))
