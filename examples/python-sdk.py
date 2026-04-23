#!/usr/bin/env python3
"""
File Share Cloud - Python SDK 示例
"""

import os
import requests


SERVER_URL = os.getenv("FILE_SHARE_URL", "http://localhost:8080")


class FileShareClient:
    """File Share Cloud Python SDK"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key} if api_key else {}
        self._session = requests.Session()

    def register(self, agent_id: str) -> dict:
        """注册新 Agent

        Args:
            agent_id: Agent 唯一标识符

        Returns:
            包含 agent_id, api_key 的字典
        """
        resp = self._session.post(f"{SERVER_URL}/register/{agent_id}")
        resp.raise_for_status()
        result = resp.json()
        self.api_key = result["api_key"]
        self.headers = {"X-API-Key": self.api_key}
        print(f"✓ Registered as {agent_id}")
        print(f"  API Key: {self.api_key[:20]}...")
        return result

    def upload(self, filepath: str, tags: list = None) -> dict:
        """上传文件

        Args:
            filepath: 文件路径
            tags: 可选，标签列表

        Returns:
            包含 file_id, filename, file_size 等信息的字典
        """
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            files = {"file": (filename, f)}
            data = {"tags": ",".join(tags)} if tags else {}
            resp = self._session.post(
                f"{SERVER_URL}/upload",
                files=files,
                data=data,
                headers=self.headers
            )
        resp.raise_for_status()
        result = resp.json()
        print(f"✓ Uploaded: {result['filename']} ({result['file_size']} bytes)")
        print(f"  File ID: {result['file_id']}")
        return result

    def upload_text(self, content: str, filename: str, tags: list = None) -> dict:
        """上传文本内容

        Args:
            content: 文本内容
            filename: 文件名
            tags: 可选，标签列表

        Returns:
            包含 file_id 等信息的字典
        """
        data = {"content": content, "filename": filename}
        if tags:
            data["tags"] = ",".join(tags)
        resp = self._session.post(
            f"{SERVER_URL}/upload/text",
            data=data,
            headers=self.headers
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"✓ Uploaded text: {filename}")
        return result

    def create_share(
        self,
        file_id: str,
        expires_hours: int = 24,
        max_downloads: int = None,
        password: str = None
    ) -> dict:
        """创建分享链接

        Args:
            file_id: 文件 ID
            expires_hours: 有效期（小时）
            max_downloads: 最大下载次数
            password: 访问密码

        Returns:
            包含 share_code, share_url 等信息的字典
        """
        params = {"expires_hours": expires_hours}
        if max_downloads:
            params["max_downloads"] = max_downloads
        if password:
            params["password"] = password

        resp = self._session.post(
            f"{SERVER_URL}/share/{file_id}",
            params=params,
            headers=self.headers
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"✓ Share created:")
        print(f"  URL: {result['share_url']}")
        print(f"  Expires in: {result['expires_in']} seconds")
        if result.get("max_downloads"):
            print(f"  Max downloads: {result['max_downloads']}")
        return result

    def download_by_share(self, share_code: str, password: str = None) -> bytes:
        """通过分享码下载（无需认证）

        Args:
            share_code: 分享码
            password: 可选，访问密码

        Returns:
            文件内容（bytes）
        """
        if password:
            resp = self._session.post(
                f"{SERVER_URL}/s/{share_code}",
                data={"password": password}
            )
        else:
            resp = self._session.get(f"{SERVER_URL}/s/{share_code}")
        resp.raise_for_status()
        print(f"✓ Downloaded via share code: {share_code}")
        return resp.content

    def download(self, file_id: str) -> bytes:
        """通过文件 ID 下载（需要认证）

        Args:
            file_id: 文件 ID

        Returns:
            文件内容（bytes）
        """
        resp = self._session.get(
            f"{SERVER_URL}/files/{file_id}/download",
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.content

    def list_files(self, search: str = None, limit: int = 100) -> list:
        """列出文件

        Args:
            search: 可选，搜索关键词
            limit: 返回数量限制

        Returns:
            文件列表
        """
        params = {"limit": limit}
        if search:
            params["search"] = search

        resp = self._session.get(
            f"{SERVER_URL}/files",
            params=params,
            headers=self.headers
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"✓ Found {result['total']} files")
        return result["files"]

    def get_file_info(self, file_id: str) -> dict:
        """获取文件信息"""
        resp = self._session.get(
            f"{SERVER_URL}/files/{file_id}",
            headers=self.headers
        )
        resp.raise_for_status()
        return resp.json()

    def get_share_info(self, share_code: str) -> dict:
        """获取分享信息（无需认证）"""
        resp = self._session.get(f"{SERVER_URL}/s/{share_code}/info")
        resp.raise_for_status()
        return resp.json()

    def delete_file(self, file_id: str) -> dict:
        """删除文件"""
        resp = self._session.delete(
            f"{SERVER_URL}/files/{file_id}",
            headers=self.headers
        )
        resp.raise_for_status()
        print(f"✓ Deleted file: {file_id}")
        return resp.json()

    def get_stats(self) -> dict:
        """获取存储统计"""
        resp = self._session.get(
            f"{SERVER_URL}/stats",
            headers=self.headers
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"✓ Storage stats:")
        print(f"  Files: {result['file_count']}")
        print(f"  Used: {result['storage_used'] / 1024 / 1024:.2f} MB")
        print(f"  Quota: {result['storage_quota'] / 1024 / 1024 / 1024:.2f} GB")
        return result


def main():
    """演示 File Share Cloud 的基本用法"""

    print("=" * 50)
    print("File Share Cloud - Python SDK Demo")
    print("=" * 50)
    print()

    # 创建两个客户端（模拟两个 Agent）
    client_a = FileShareClient()
    client_b = FileShareClient()

    # ===== Agent A: 上传并分享 =====

    print("\n[Agent A] 注册...")
    client_a.register("demo-agent-alpha")

    print("\n[Agent A] 上传文件...")
    # 创建一个测试文件
    with open("/tmp/demo-file.txt", "w") as f:
        f.write("Hello from File Share Cloud!\nThis is a demo file.")
    result = client_a.upload("/tmp/demo-file.txt", tags=["demo", "test"])

    print("\n[Agent A] 创建分享链接（24小时有效，最多5次下载）...")
    share = client_a.create_share(
        result["file_id"],
        expires_hours=24,
        max_downloads=5
    )
    share_code = share["share_code"]

    # ===== Agent B: 通过分享码下载 =====

    print("\n[Agent B] 通过分享码下载（无需注册！）...")
    content = client_b.download_by_share(share_code)
    print(f"  Downloaded: {content.decode()}")

    print("\n[Agent B] 查看分享信息...")
    share_info = client_b.get_share_info(share_code)
    print(f"  Filename: {share_info['filename']}")
    print(f"  Size: {share_info['file_size']} bytes")
    print(f"  Downloads: {share_info['download_count']}")

    # ===== 清理 =====

    print("\n[Agent A] 查看存储统计...")
    client_a.get_stats()

    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
