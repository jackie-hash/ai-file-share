"""File Share Cloud - AI Agent 文件共享服务 v2

支持多Agent之间的文件快速共享功能
"""
import os
import tempfile
import secrets
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Depends, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from auth import generate_api_key, hash_api_key
from database import db
from storage import storage
from models import (
    RegisterResponse, UploadResponse, ShareResponse, ShareInfo,
    FileListResponse, FileListItem, DeleteResponse
)


# 配置
SERVER_URL = os.getenv("SERVER_URL", "http://82.157.208.246:8080")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 File Share Cloud v2 启动中...")
    print(f"📂 存储路径: {os.getenv('STORAGE_PATH', '/data/files')}")
    print(f"🔗 服务地址: {SERVER_URL}")
    yield
    print("👋 File Share Cloud 已关闭")


app = FastAPI(
    title="File Share Cloud",
    description="AI Agent 文件共享服务 - 支持多Agent之间的文件快速分享",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_agent_id(x_api_key: Annotated[str, Header(alias="X-API-Key")] = None) -> str:
    """依赖：验证并获取当前 Agent ID"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    if not x_api_key.startswith("fsc_"):
        raise HTTPException(status_code=401, detail="Invalid API Key format")

    key_hash = hash_api_key(x_api_key)
    agent = db.get_agent_by_key_hash(key_hash)

    if not agent:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    db.update_agent_last_seen(agent["id"])
    return agent["id"]


# ========== 健康检查 ==========

@app.get("/health", summary="健康检查")
async def health_check():
    return {"status": "ok", "service": "file-share-cloud", "version": "2.0.0"}


@app.get("/", summary="服务信息")
async def root():
    return {
        "service": "File Share Cloud v2",
        "version": "2.0.0",
        "description": "AI Agent 文件共享服务",
        "docs": "/docs",
        "endpoints": {
            "register": "POST /register/{agent_id}",
            "upload": "POST /upload",
            "list": "GET /files",
            "share": "POST /share/{file_id}",
            "download": "GET /s/{share_code}",
            "download_with_password": "POST /s/{share_code}"
        }
    }


# ========== Agent 注册 ==========

@app.post("/register/{agent_id}", response_model=RegisterResponse, summary="注册新Agent")
async def register(agent_id: str):
    """注册一个新 Agent，返回 API Key"""
    # 检查是否已存在
    agents = db.list_agents()
    if any(a["id"] == agent_id for a in agents):
        raise HTTPException(status_code=400, detail="Agent ID already exists")

    # 生成 API Key
    raw_key, key_hash, key_prefix = generate_api_key()

    # 存储到数据库
    db.create_agent(agent_id, key_hash)

    return RegisterResponse(
        agent_id=agent_id,
        api_key=raw_key,
        message="请妥善保管 API Key，这是唯一的访问凭证"
    )


@app.post("/register/{agent_id}/force", response_model=RegisterResponse, summary="强制注册(覆盖)")
async def register_force(agent_id: str):
    """强制注册，会覆盖已存在的 Agent"""
    raw_key, key_hash, key_prefix = generate_api_key()
    db.create_agent(agent_id, key_hash)

    return RegisterResponse(
        agent_id=agent_id,
        api_key=raw_key,
        message="Agent 已创建，API Key 已更新"
    )


# ========== 文件上传 ==========

@app.post("/upload", response_model=UploadResponse, summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    tags: str = Form(None, description="逗号分隔的标签"),
    agent_id: str = Depends(get_agent_id)
):
    """上传文件到 Agent 的存储空间"""
    try:
        # 检查配额
        storage_info = db.get_agent_storage(agent_id)
        if storage_info["storage_used"] >= storage_info["storage_quota"]:
            raise HTTPException(status_code=413, detail="存储配额已用完")

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # 存储文件
            result = await storage.upload(agent_id, tmp_path, file.filename)

            # 检查是否重复（基于内容哈希）
            existing = db.get_file_by_hash(result["content_hash"], agent_id)
            if existing:
                # 重复文件，删除刚上传的，返回已存在的
                storage.delete(result["file_path"])
                file_info = db.get_file_by_id(existing["id"])
                share = db.get_file_shares(existing["id"])
                share_code = share[0]["share_code"] if share else None

                return UploadResponse(
                    filename=file_info["original_filename"],
                    file_size=file_info["file_size"],
                    file_id=file_info["id"],
                    url=f"{SERVER_URL}/files/{file_info['id']}",
                    share_code=share_code
                )

            # 解析标签
            tag_list = [t.strip() for t in tags.split(",")] if tags else []

            # 记录到数据库
            db.create_file(
                file_id=result["file_id"],
                filename=result["stored_filename"],
                original_filename=result["filename"],
                file_path=result["file_path"],
                file_size=result["file_size"],
                content_type=file.content_type or "application/octet-stream",
                agent_id=agent_id,
                content_hash=result["content_hash"],
                tags=tag_list
            )

            return UploadResponse(
                filename=result["filename"],
                file_size=result["file_size"],
                file_id=result["file_id"],
                url=f"{SERVER_URL}/files/{result['file_id']}"
            )
        finally:
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/text", summary="上传文本内容")
async def upload_text(
    content: str = Form(...),
    filename: str = Form(...),
    tags: str = Form(None),
    agent_id: str = Depends(get_agent_id)
):
    """直接上传文本内容"""
    content_bytes = content.encode("utf-8")

    result = await storage.upload_bytes(agent_id, content_bytes, filename)

    # 检查重复
    existing = db.get_file_by_hash(result["content_hash"], agent_id)
    if existing:
        share = db.get_file_shares(existing["id"])
        share_code = share[0]["share_code"] if share else None
        file_info = db.get_file_by_id(existing["id"])
        return UploadResponse(
            filename=file_info["original_filename"],
            file_size=file_info["file_size"],
            file_id=file_info["id"],
            url=f"{SERVER_URL}/files/{file_info['id']}",
            share_code=share_code
        )

    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    db.create_file(
        file_id=result["file_id"],
        filename=result["stored_filename"],
        original_filename=result["filename"],
        file_path=result["file_path"],
        file_size=result["file_size"],
        content_type="text/plain",
        agent_id=agent_id,
        content_hash=result["content_hash"],
        tags=tag_list
    )

    return UploadResponse(
        filename=result["filename"],
        file_size=result["file_size"],
        file_id=result["file_id"],
        url=f"{SERVER_URL}/files/{result['file_id']}"
    )


# ========== 文件列表 ==========

@app.get("/files", response_model=FileListResponse, summary="列出文件")
async def list_files(
    agent_id: str = Depends(get_agent_id),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: str = Query(None, description="搜索文件名或标签")
):
    """列出 Agent 的所有文件"""
    if search:
        files = db.search_files(agent_id, search)
    else:
        files = db.list_files(agent_id, limit, offset)

    file_items = []
    for f in files:
        tags = json.loads(f.get("tags", "[]")) if f.get("tags") else []
        shares = db.get_file_shares(f["id"])
        share_code = shares[0]["share_code"] if shares else None

        file_items.append(FileListItem(
            id=f["id"],
            filename=f["original_filename"],
            file_size=f["file_size"],
            file_id=f["id"],
            content_type=f.get("content_type", "application/octet-stream"),
            created_at=f["created_at"],
            tags=tags,
            share_code=share_code
        ))

    total = db.count_files(agent_id)

    return FileListResponse(files=file_items, total=total)


@app.get("/files/{file_id}", summary="获取文件信息")
async def get_file(file_id: str, agent_id: str = Depends(get_agent_id)):
    """获取单个文件的信息"""
    file_info = db.get_file_by_id(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if file_info["agent_id"] != agent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    tags = json.loads(file_info.get("tags", "[]")) if file_info.get("tags") else []
    shares = db.get_file_shares(file_id)

    return {
        "id": file_info["id"],
        "filename": file_info["original_filename"],
        "file_size": file_info["file_size"],
        "content_type": file_info.get("content_type"),
        "created_at": file_info["created_at"],
        "tags": tags,
        "shares": [{"share_code": s["share_code"], "expires_at": s["expires_at"]} for s in shares]
    }


# ========== 文件下载(认证) ==========

@app.get("/files/{file_id}/download", summary="下载文件")
async def download_file(
    file_id: str,
    agent_id: str = Depends(get_agent_id)
):
    """下载文件（需要认证）"""
    file_info = db.get_file_by_id(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    content = storage.get_file_content(file_info["file_path"])
    if not content:
        raise HTTPException(status_code=404, detail="File content not found")

    import mimetypes
    media_type = mimetypes.guess_type(file_info["original_filename"])[0] or "application/octet-stream"

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_info['original_filename']}"}
    )


# ========== 分享功能 ==========

@app.post("/share/{file_id}", response_model=ShareResponse, summary="创建分享链接")
async def create_share(
    file_id: str,
    expires_hours: int = Query(24, ge=1, le=168, description="分享有效期(小时)"),
    max_downloads: int = Query(None, ge=1, description="最大下载次数"),
    password: str = Query(None, description="访问密码"),
    agent_id: str = Depends(get_agent_id)
):
    """为文件创建分享链接"""
    file_info = db.get_file_by_id(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if file_info["agent_id"] != agent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 如果文件已经有活跃分享，返回现有的
    existing_shares = db.get_file_shares(file_id)
    for s in existing_shares:
        if s.get("is_active"):
            return ShareResponse(
                share_code=s["share_code"],
                share_url=f"{SERVER_URL}/s/{s['share_code']}",
                expires_in=int((datetime.fromisoformat(s["expires_at"]) - datetime.utcnow()).total_seconds()) if s.get("expires_at") else 0,
                max_downloads=s.get("max_downloads"),
                download_count=s["download_count"]
            )

    # 创建新分享
    share = db.create_share(
        file_id=file_id,
        creator_agent_id=agent_id,
        expires_hours=expires_hours,
        max_downloads=max_downloads,
        password=password
    )

    return ShareResponse(
        share_code=share["share_code"],
        share_url=f"{SERVER_URL}/s/{share['share_code']}",
        expires_in=expires_hours * 3600,
        max_downloads=max_downloads,
        download_count=0
    )


@app.post("/s/{share_code}", summary="通过分享码下载(带密码)")
async def download_with_password(
    share_code: str,
    password: str = Form(None)
):
    """通过分享码下载文件（支持密码）"""
    valid, error, share = db.validate_share(share_code, password)

    if not valid:
        raise HTTPException(status_code=403, detail=error)

    file_info = {
        "original_filename": share["filename"],
        "file_path": share["file_path"],
        "file_size": share["file_size"]
    }

    content = storage.get_file_content(share["file_path"])
    if not content:
        raise HTTPException(status_code=404, detail="File not found")

    # 记录下载
    db.increment_download_count(share["id"])
    db.log_download(share["id"], share["file_id"])

    import mimetypes
    media_type = mimetypes.guess_type(share["filename"])[0] or "application/octet-stream"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={share['filename']}",
            "X-Share-Code": share_code,
            "X-Download-Count": str(share["download_count"] + 1)
        }
    )


@app.get("/s/{share_code}", summary="通过分享码下载")
async def download_by_share(
    share_code: str,
    password: str = Query(None)
):
    """通过分享码下载文件"""
    valid, error, share = db.validate_share(share_code, password)

    if not valid:
        raise HTTPException(status_code=403, detail=error)

    if share.get("password_protected") and password != share["password_protected"]:
        raise HTTPException(status_code=403, detail="Password required")

    content = storage.get_file_content(share["file_path"])
    if not content:
        raise HTTPException(status_code=404, detail="File not found")

    db.increment_download_count(share["id"])
    db.log_download(share["id"], share["file_id"])

    import mimetypes
    media_type = mimetypes.guess_type(share["filename"])[0] or "application/octet-stream"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={share['filename']}",
            "X-Share-Code": share_code
        }
    )


@app.get("/s/{share_code}/info", summary="获取分享信息")
async def get_share_info(share_code: str):
    """获取分享的基本信息（不暴露下载）"""
    valid, error, share = db.validate_share(share_code)

    if not valid:
        raise HTTPException(status_code=403, detail=error)

    return {
        "filename": share["filename"],
        "file_size": share["file_size"],
        "expires_at": share["expires_at"],
        "download_count": share["download_count"],
        "max_downloads": share["max_downloads"],
        "password_protected": bool(share.get("password_protected"))
    }


@app.delete("/share/{share_id}", summary="删除分享")
async def delete_share(share_id: str, agent_id: str = Depends(get_agent_id)):
    """删除分享链接"""
    success = db.deactivate_share(share_id, agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Share not found")
    return {"success": True, "message": "Share deleted"}


# ========== 文件删除 ==========

@app.delete("/files/{file_id}", response_model=DeleteResponse, summary="删除文件")
async def delete_file(file_id: str, agent_id: str = Depends(get_agent_id)):
    """删除文件"""
    file_info = db.get_file_by_id(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if file_info["agent_id"] != agent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # 删除物理文件
    storage.delete(file_info["file_path"])

    # 删除数据库记录
    db.delete_file(file_id, agent_id)

    return DeleteResponse(success=True, message=f"File '{file_info['original_filename']}' deleted")


@app.delete("/files/{file_id}/tags", summary="清除文件标签")
async def clear_tags(file_id: str, agent_id: str = Depends(get_agent_id)):
    """清除文件标签"""
    file_info = db.get_file_by_id(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")

    if file_info["agent_id"] != agent_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.update_file_tags(file_id, [])
    return {"success": True}


# ========== 存储统计 ==========

@app.get("/stats", summary="获取存储统计")
async def get_stats(agent_id: str = Depends(get_agent_id)):
    """获取 Agent 的存储统计"""
    file_stats = db.get_file_stats(agent_id)
    storage_info = db.get_agent_storage(agent_id)

    return {
        "file_count": file_stats["file_count"],
        "total_size": file_stats["total_size"],
        "storage_used": storage_info["storage_used"],
        "storage_quota": storage_info["storage_quota"],
        "usage_percent": round(storage_info["storage_used"] / storage_info["storage_quota"] * 100, 2) if storage_info["storage_quota"] > 0 else 0
    }


# ========== 管理接口 ==========

@app.get("/admin/agents", summary="列出所有Agent")
async def list_agents():
    """列出所有注册的 Agent"""
    agents = db.list_agents()
    return {
        "total": len(agents),
        "agents": [{"id": a["id"], "created_at": a["created_at"], "last_seen": a.get("last_seen")} for a in agents]
    }


# 需要添加 json 导入
import json
from datetime import datetime


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
