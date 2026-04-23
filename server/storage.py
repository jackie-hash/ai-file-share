"""文件存储 - 本地文件系统"""
import os
import shutil
import hashlib
import secrets
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class FileStorage:
    """文件存储管理器"""

    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.getenv("STORAGE_PATH", "/data/files")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_agent_dir(self, agent_id: str) -> Path:
        """获取 Agent 的专属目录"""
        agent_dir = self.base_path / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        return agent_dir

    def _generate_file_id(self) -> str:
        """生成唯一文件ID"""
        return secrets.token_hex(16)

    def _generate_stored_filename(self) -> str:
        """生成存储文件名（无冲突）"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        random_str = secrets.token_hex(4)
        return f"{timestamp}_{random_str}"

    def compute_content_hash(self, content: bytes) -> str:
        """计算内容哈希（用于去重）"""
        return hashlib.sha256(content).hexdigest()

    def compute_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def upload(self, agent_id: str, source_path: str, original_filename: str) -> dict:
        """上传文件（从本地路径）"""
        file_id = self._generate_file_id()
        agent_dir = self._get_agent_dir(agent_id)

        # 计算内容哈希（用于去重）
        content_hash = self.compute_file_hash(Path(source_path))

        # 生成存储文件名
        stored_filename = self._generate_stored_filename()
        ext = Path(original_filename).suffix
        stored_path = agent_dir / f"{stored_filename}{ext}"

        # 复制文件
        shutil.copy2(source_path, stored_path)
        stat = stored_path.stat()

        return {
            "file_id": file_id,
            "filename": original_filename,  # 原始文件名
            "stored_filename": f"{stored_filename}{ext}",
            "file_path": str(stored_path),
            "file_size": stat.st_size,
            "content_hash": content_hash,
            "created_at": datetime.fromtimestamp(stat.st_ctime)
        }

    async def upload_bytes(self, agent_id: str, content: bytes, original_filename: str) -> dict:
        """直接上传字节内容"""
        file_id = self._generate_file_id()
        agent_dir = self._get_agent_dir(agent_id)

        # 计算内容哈希
        content_hash = self.compute_content_hash(content)

        # 生成存储文件名
        stored_filename = self._generate_stored_filename()
        ext = Path(original_filename).suffix if '.' in original_filename else ''
        stored_path = agent_dir / f"{stored_filename}{ext}"

        # 写入文件
        with open(stored_path, 'wb') as f:
            f.write(content)

        return {
            "file_id": file_id,
            "filename": original_filename,
            "stored_filename": f"{stored_filename}{ext}",
            "file_path": str(stored_path),
            "file_size": len(content),
            "content_hash": content_hash,
            "created_at": datetime.utcnow()
        }

    def get_file_content(self, file_path: str) -> Optional[bytes]:
        """获取文件内容"""
        p = Path(file_path)
        if p.exists() and p.is_file():
            return p.read_bytes()
        return None

    def delete(self, file_path: str) -> bool:
        """删除文件"""
        p = Path(file_path)
        if p.exists() and p.is_file():
            p.unlink()
            return True
        return False

    def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        p = Path(file_path)
        return p.exists() and p.is_file()

    def get_stats(self, agent_id: str) -> dict:
        """获取存储统计"""
        agent_dir = self._get_agent_dir(agent_id)
        if not agent_dir.exists():
            return {"total_files": 0, "total_size": 0}

        files = list(agent_dir.iterdir())
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        return {
            "total_files": len([f for f in files if f.is_file()]),
            "total_size": total_size
        }


# 全局存储实例
storage = FileStorage()
