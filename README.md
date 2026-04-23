# File Share Cloud

> 🤖 AI Agent 文件共享服务 - 支持多 Agent 之间的文件快速分享

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/intrust/ai-file-share)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)](https://www.python.org/)

## 📖 简介

File Share Cloud 是一个专为 AI Agent 设计的文件共享服务。它允许不同的 AI Agent 之间快速、安全地共享文件，同时支持生成分享链接让任何人都能下载文件。

### 核心特性

- 🔗 **无需注册下载**: 生成分享码后，任何人都可以直接下载，无需注册账号
- 🤖 **Agent 原生支持**: 专为 AI Agent 设计，提供简洁的 API
- ⚡ **快速分享**: 几步操作即可创建分享链接
- 🔒 **访问控制**: 支持密码保护、下载次数限制、过期时间
- 📊 **存储配额**: 每个 Agent 独立存储空间，默认 10GB
- 🔍 **文件去重**: 相同内容的文件只存储一份，节省空间

## 🚀 快速开始

### 部署服务

```bash
# 克隆项目
git clone https://github.com/intrust/ai-file-share.git
cd ai-file-share

# 启动服务 (需要 Docker)
docker-compose up -d

# 或手动启动
cd server
docker build -t file-share-cloud .
docker run -d -p 8080:8080 \
  -v file-share-data:/data \
  -v file-share-db:/data/db \
  -e STORAGE_PATH=/data/files \
  -e DB_PATH=/data/db/file_share.db \
  -e SERVER_URL=http://your-domain.com:8080 \
  file-share-cloud
```

服务启动后访问: http://localhost:8080

### 5 分钟入门

**Step 1: 注册 Agent**

```bash
curl -X POST http://localhost:8080/register/my-agent
```

返回:
```json
{
  "agent_id": "my-agent",
  "api_key": "fsc_xxx...",
  "message": "请妥善保管 API Key，这是唯一的访问凭证"
}
```

**Step 2: 上传文件**

```bash
curl -X POST -F "file=@/path/to/file.pdf" \
     -H "X-API-Key: fsc_xxx..." \
     http://localhost:8080/upload
```

**Step 3: 创建分享链接**

```bash
curl -X POST "http://localhost:8080/share/{file_id}?expires_hours=24" \
     -H "X-API-Key: fsc_xxx..."
```

返回:
```json
{
  "share_code": "abc12345",
  "share_url": "http://localhost:8080/s/abc12345",
  "expires_in": 86400
}
```

**Step 4: 分享给他人（无需认证！）**

```bash
curl http://localhost:8080/s/abc12345
# 直接返回文件内容
```

## 📚 API 文档

### 基础信息

- **Base URL**: `http://localhost:8080`
- **认证方式**: Header `X-API-Key: {your_api_key}`
- **返回格式**: JSON

### Agent 注册

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/register/{agent_id}` | 注册新 Agent |

```bash
# 请求
POST /register/my-agent

# 响应
{
  "agent_id": "my-agent",
  "api_key": "fsc_xxxxxxxxxxxxxxxxxxxx",
  "message": "请妥善保管 API Key，这是唯一的访问凭证"
}
```

### 文件管理

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/upload` | 上传文件 | API Key |
| GET | `/files` | 列出文件 | API Key |
| GET | `/files/{file_id}` | 获取文件信息 | API Key |
| GET | `/files/{file_id}/download` | 下载文件 | API Key |
| DELETE | `/files/{file_id}` | 删除文件 | API Key |

```bash
# 上传文件（支持标签）
curl -X POST -F "file=@document.pdf" \
                   -F "tags=report,2024,q1" \
                   -H "X-API-Key: fsc_xxx" \
                   http://localhost:8080/upload

# 列出文件
curl -H "X-API-Key: fsc_xxx" http://localhost:8080/files

# 搜索文件
curl -H "X-API-Key: fsc_xxx" "http://localhost:8080/files?search=report"
```

### 分享功能

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/share/{file_id}` | 创建分享链接 | API Key |
| GET | `/s/{share_code}` | 下载（分享） | ❌ 无需认证 |
| GET | `/s/{share_code}/info` | 获取分享信息 | ❌ 无需认证 |
| DELETE | `/share/{share_id}` | 删除分享 | API Key |

```bash
# 创建分享链接（24小时有效，最多10次下载）
curl -X POST "http://localhost:8080/share/{file_id}?expires_hours=24&max_downloads=10" \
     -H "X-API-Key: fsc_xxx"

# 创建带密码的分享
curl -X POST "http://localhost:8080/share/{file_id}?expires_hours=24&password=secret" \
     -H "X-API-Key: fsc_xxx"

# 下载（无需认证）
curl http://localhost:8080/s/abc12345

# 带密码下载
curl -X POST http://localhost:8080/s/abc12345 -d "password=secret"
```

### 其他

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/health` | 健康检查 | ❌ |
| GET | `/stats` | 存储统计 | API Key |
| GET | `/admin/agents` | 列出所有 Agent | ❌ |

## 💻 客户端示例

### Python SDK

```python
import requests

SERVER_URL = "http://localhost:8080"

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

    def create_share(self, file_id: str, expires_hours: int = 24, max_downloads: int = None, password: str = None) -> dict:
        """创建分享链接"""
        params = {"expires_hours": expires_hours}
        if max_downloads:
            params["max_downloads"] = max_downloads
        if password:
            params["password"] = password
        resp = requests.post(f"{SERVER_URL}/share/{file_id}", params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def download_by_share(self, share_code: str) -> bytes:
        """通过分享码下载（无需认证）"""
        resp = requests.get(f"{SERVER_URL}/s/{share_code}")
        resp.raise_for_status()
        return resp.content

    def list_files(self, search: str = None) -> dict:
        """列出文件"""
        params = {"search": search} if search else {}
        resp = requests.get(f"{SERVER_URL}/files", params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def get_stats(self) -> dict:
        """获取存储统计"""
        resp = requests.get(f"{SERVER_URL}/stats", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def delete_file(self, file_id: str) -> dict:
        """删除文件"""
        resp = requests.delete(f"{SERVER_URL}/files/{file_id}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()
```

### 使用示例

```python
# Agent A: 上传并分享
client_a = FileShareClient()
client_a.register("agent-alpha")

# 上传文件
result = client_a.upload("/tmp/report.pdf", tags=["report", "monthly"])
print(f"File ID: {result['file_id']}")

# 创建分享链接（7天有效，最多50次下载）
share = client_a.create_share(result["file_id"], expires_hours=168, max_downloads=50)
print(f"Share URL: {share['share_url']}")
# Output: Share URL: http://localhost:8080/s/XMDuXMLx

# Agent B: 直接下载（无需注册！）
client_b = FileShareClient()
content = client_b.download_by_share(share["share_code"])
print(f"Downloaded: {len(content)} bytes")
```

### Hermes Agent Skill

如果你使用 Hermes Agent，可以直接安装 skill：

```
file-share-cloud
```

然后在 Agent 中使用：

```python
# 在 Hermes Agent 中
skill: file-share-cloud

# 上传并分享
await agent.run_skill("file-share-cloud:upload", {"filepath": "/tmp/data.csv"})
share_url = await agent.run_skill("file-share-cloud:share", {"file_id": "xxx"})

# 下载
content = await agent.run_skill("file-share-cloud:download-by-share", {"share_code": "abc123"})
```

## 🐳 Docker 部署

### Docker Compose

```yaml
version: '3.8'

services:
  file-share-cloud:
    image: file-share-cloud
    container_name: file-share-cloud
    ports:
      - "8080:8080"
    volumes:
      - file-share-data:/data
      - file-share-db:/data/db
    environment:
      - STORAGE_PATH=/data/files
      - DB_PATH=/data/db/file_share.db
      - SERVER_URL=http://your-domain.com:8080
    restart: unless-stopped

volumes:
  file-share-data:
  file-share-db:
```

### 生产环境建议

1. **使用 Nginx 反向代理** + SSL 证书
2. **定期备份数据库和存储卷**
3. **监控存储使用量**
4. **设置防火墙规则**

```nginx
# /etc/nginx/conf.d/file-share.conf
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    File Share Cloud                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌─────────┐    ┌─────────┐    ┌─────────────────┐   │
│   │ 注册Agent │    │ 上传文件  │    │ 创建分享链接     │   │
│   └────┬────┘    └────┬────┘    └────────┬────────┘   │
│        │               │                  │              │
│        └───────────────┼──────────────────┘              │
│                        ▼                                 │
│              ┌────────────────────┐                     │
│              │   SQLite 元数据      │                     │
│              │  (Agent/文件/分享)  │                      │
│              └────────────┬───────┘                     │
│                         │                               │
│                        ▼                                │
│              ┌────────────────────┐                     │
│              │   本地文件系统      │                     │
│              │   /data/files      │                      │
│              └────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### 数据模型

- **Agent**: 存储空间配额、最后访问时间
- **File**: 原始文件名、存储路径、内容哈希、标签
- **Share**: 分享码、过期时间、下载次数限制、密码保护

## 📁 项目结构

```
ai-file-share/
├── README.md           # 本文档
├── LICENSE             # MIT 许可证
├── CONTRIBUTING.md      # 贡献指南
├── CODE_OF_CONDUCT.md  # 行为准则
├── docker-compose.yml  # Docker Compose 配置
├── server/
│   ├── Dockerfile      # Docker 镜像构建
│   ├── requirements.txt # Python 依赖
│   ├── main.py         # FastAPI 主程序
│   ├── database.py     # SQLite 数据库操作
│   ├── storage.py      # 文件存储管理
│   ├── auth.py         # 认证工具
│   └── models.py       # Pydantic 数据模型
├── skill/              # Hermes Agent Skill
│   └── SKILL.md
└── examples/           # 使用示例
    ├── python-sdk.py
    └── curl-commands.sh
```

## 🛡️ 安全考虑

1. **API Key 安全**: API Key 是访问凭证，请妥善保管
2. **密码保护**: 敏感文件分享建议设置密码
3. **下载限制**: 重要文件设置最大下载次数
4. **过期时间**: 定期清理过期分享
5. **存储隔离**: 每个 Agent 的文件存储在独立目录

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [SQLite](https://www.sqlite.org/) - 轻量级数据库
- [Uvicorn](https://www.uvicorn.org/) - ASGI 服务器

---

<p align="center">
  用 ❤️ 为 AI Agent 构建 | 如果对你有帮助，请给个 ⭐
</p>
