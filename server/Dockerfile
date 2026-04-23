FROM python:3.11-slim

WORKDIR /app

# 使用清华镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p /data/files /data/db

# 环境变量
ENV STORAGE_PATH=/data/files
ENV DB_PATH=/data/db/file_share.db
ENV PORT=8080
ENV HOST=0.0.0.0
ENV SERVER_URL=http://localhost:8080

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# 启动命令 - 使用 -m 以支持相对导入
CMD ["python", "-m", "main"]
