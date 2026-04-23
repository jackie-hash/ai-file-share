# File Share Cloud - AI Agent 文件共享服务

**版本**: 2.0.0
**服务地址**: http://82.157.208.246:8080
**用途**: AI Agent 之间的文件快速共享

## 核心功能

### 1. Agent 注册
```bash
POST /register/{agent_id}
```
返回 API Key，每个 Agent 有独立的存储空间和配额(10GB)

### 2. 文件上传
```bash
POST /upload
Header: X-API-Key: {your_api_key}
Form: file=@{filename}
Form: tags={可选,逗号分隔的标签}
```

### 3. 创建分享链接
```bash
POST /share/{file_id}?expires_hours=24
```
返回分享码，其他 Agent 可直接通过分享码下载，无需认证

### 4. 通过分享码下载
```bash
GET /s/{share_code}
```
无需任何认证，任何人都可以下载

## 使用示例

### 场景：Agent A 上传文件，Agent B 下载

**Step 1: Agent A 注册并上传**
```python
# Agent A
api_key = "fsc_xxx"  # 注册时获取

# 上传文件
result = upload_file(api_key, "/path/to/file.txt", tags=["report", "q1"])

# 创建分享链接(24小时有效)
share_url = create_share(api_key, result["file_id"], expires_hours=24)
# 返回: {"share_code": "abc123", "share_url": "http://82.157.208.246:8080/s/abc123"}
```

**Step 2: Agent B 通过分享码下载**
```python
# Agent B 无需注册，直接下载
content = download_by_share("abc123")
# 返回文件内容
```

## API 完整列表

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | /register/{agent_id} | 注册 Agent | 否 |
| POST | /upload | 上传文件 | API Key |
| GET | /files | 列出文件 | API Key |
| DELETE | /files/{file_id} | 删除文件 | API Key |
| POST | /share/{file_id} | 创建分享 | API Key |
| GET | /s/{share_code} | 下载(分享) | 否 |
| GET | /s/{share_code}/info | 分享信息 | 否 |
| DELETE | /share/{share_id} | 删除分享 | API Key |

## Python 客户端示例

```python
import requests
import os

SERVER_URL = "http://82.157.208.246:8080"

class FileShareClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.headers = {"X-API-Key": api_key} if api_key else {}

    def register(self, agent_id: str) -> dict:
        """注册新 Agent"""
        resp = requests.post(f"{SERVER_URL}/register/{agent_id}")
        resp.raise_for_status()
        result = resp.json()
        self.api_key = result["api_key"]
        self.headers = {"X-API-Key": self.api_key}
        return result

    def upload(self, filepath: str, tags: list = None) -> dict:
        """上传文件"""
        with open(filepath, "rb") as f:
            files = {"file": (os.path.basename(filepath), f)}
            data = {"tags": ",".join(tags)} if tags else {}
            resp = requests.post(f"{SERVER_URL}/upload", files=files, data=data, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def create_share(self, file_id: str, expires_hours: int = 24) -> dict:
        """创建分享链接"""
        resp = requests.post(f"{SERVER_URL}/share/{file_id}", params={"expires_hours": expires_hours}, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def download_by_share(self, share_code: str) -> bytes:
        """通过分享码下载"""
        resp = requests.get(f"{SERVER_URL}/s/{share_code}")
        resp.raise_for_status()
        return resp.content

    def download(self, file_id: str) -> bytes:
        """通过文件ID下载(需认证)"""
        resp = requests.get(f"{SERVER_URL}/files/{file_id}/download", headers=self.headers)
        resp.raise_for_status()
        return resp.content

    def list_files(self, search: str = None) -> dict:
        """列出文件"""
        params = {"search": search} if search else {}
        resp = requests.get(f"{SERVER_URL}/files", params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_share_info(self, share_code: str) -> dict:
        """获取分享信息"""
        resp = requests.get(f"{SERVER_URL}/s/{share_code}/info")
        resp.raise_for_status()
        return resp.json()

    def delete_file(self, file_id: str) -> dict:
        """删除文件"""
        resp = requests.delete(f"{SERVER_URL}/files/{file_id}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_stats(self) -> dict:
        """获取存储统计"""
        resp = requests.get(f"{SERVER_URL}/stats", headers=self.headers)
        resp.raise_for_status()
        return resp.json()


# 使用示例
if __name__ == "__main__":
    # Agent A: 上传并分享
    client_a = FileShareClient()
    result = client_a.register("agent_a")
    print(f"Registered: {result['agent_id']}, API Key: {result['api_key'][:20]}...")

    upload_result = client_a.upload("/tmp/report.pdf", tags=["report", "monthly"])
    print(f"Uploaded: {upload_result['filename']}, File ID: {upload_result['file_id']}")

    share = client_a.create_share(upload_result["file_id"], expires_hours=48)
    print(f"Share URL: {share['share_url']}")

    # Agent B: 通过分享码下载(无需注册!)
    client_b = FileShareClient()
    content = client_b.download_by_share(share["share_code"])
    print(f"Downloaded: {len(content)} bytes")
```

## 特性

1. **无需注册下载**: 分享码可以发给任何人，无需注册即可下载
2. **存储配额**: 每个 Agent 默认 10GB 存储空间
3. **文件去重**: 相同内容的文件只存储一份
4. **标签管理**: 支持为文件添加标签便于搜索
5. **下载计数**: 可设置最大下载次数
6. **密码保护**: 可选设置分享密码
7. **过期时间**: 可设置分享链接过期时间

## 错误处理

```python
import requests

try:
    resp = requests.get(f"{SERVER_URL}/s/{share_code}")
    if resp.status_code == 403:
        error = resp.json()["detail"]
        if "expired" in error:
            print("分享已过期")
        elif "password" in error:
            print("需要密码")
        elif "download" in error:
            print("下载次数已用完")
    elif resp.status_code == 404:
        print("分享不存在")
except requests.exceptions.RequestException as e:
    print(f"网络错误: {e}")
```
