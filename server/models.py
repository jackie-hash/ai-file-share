"""数据模型"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RegisterResponse(BaseModel):
    agent_id: str
    api_key: str
    message: str


class UploadResponse(BaseModel):
    filename: str
    file_size: int
    file_id: str
    url: str
    share_code: Optional[str] = None  # 快速分享码


class ShareResponse(BaseModel):
    share_code: str
    share_url: str
    expires_in: int  # 秒
    max_downloads: Optional[int] = None
    download_count: int = 0


class ShareInfo(BaseModel):
    share_code: str
    filename: str
    file_size: int
    created_at: str
    expires_at: Optional[str]
    download_count: int
    max_downloads: Optional[int]


class FileListItem(BaseModel):
    file_id: str
    filename: str
    file_size: int
    content_type: str
    created_at: str
    tags: Optional[List[str]] = []
    share_code: Optional[str] = None


class FileListResponse(BaseModel):
    files: List[FileListItem]
    total: int


class DeleteResponse(BaseModel):
    success: bool
    message: str


class ErrorResponse(BaseModel):
    detail: str
