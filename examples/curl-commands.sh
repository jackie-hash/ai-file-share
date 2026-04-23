#!/bin/bash

# File Share Cloud - curl 命令示例
# 基础 URL
BASE_URL="http://localhost:8080"

echo "=== File Share Cloud curl 命令示例 ==="
echo ""

# 1. 注册 Agent
echo "1. 注册新 Agent"
echo "curl -X POST ${BASE_URL}/register/my-agent"
echo ""

# 2. 上传文件 (需要先获取 API Key)
echo "2. 上传文件"
echo 'curl -X POST -F "file=@/path/to/file.txt" \'
echo '     -H "X-API-Key: YOUR_API_KEY" \'
echo "     ${BASE_URL}/upload"
echo ""

# 3. 列出文件
echo "3. 列出文件"
echo "curl -H \"X-API-Key: YOUR_API_KEY\" ${BASE_URL}/files"
echo ""

# 4. 搜索文件
echo "4. 搜索文件"
echo "curl -H \"X-API-Key: YOUR_API_KEY\" \"${BASE_URL}/files?search=report\""
echo ""

# 5. 创建分享链接
echo "5. 创建分享链接（24小时有效）"
echo "curl -X POST \"${BASE_URL}/share/FILE_ID?expires_hours=24\" \\"
echo '     -H "X-API-Key: YOUR_API_KEY"'
echo ""

# 6. 创建带密码的分享
echo "6. 创建带密码的分享"
echo "curl -X POST \"${BASE_URL}/share/FILE_ID?expires_hours=24&password=secret\" \\"
echo '     -H "X-API-Key: YOUR_API_KEY"'
echo ""

# 7. 通过分享码下载（无需认证）
echo "7. 通过分享码下载"
echo "curl ${BASE_URL}/s/SHARE_CODE"
echo ""

# 8. 带密码下载
echo "8. 带密码下载"
echo "curl -X POST ${BASE_URL}/s/SHARE_CODE -d \"password=secret\""
echo ""

# 9. 获取分享信息
echo "9. 获取分享信息"
echo "curl ${BASE_URL}/s/SHARE_CODE/info"
echo ""

# 10. 删除文件
echo "10. 删除文件"
echo "curl -X DELETE -H \"X-API-Key: YOUR_API_KEY\" ${BASE_URL}/files/FILE_ID"
echo ""

# 11. 获取存储统计
echo "11. 获取存储统计"
echo "curl -H \"X-API-Key: YOUR_API_KEY\" ${BASE_URL}/stats"
echo ""

# 12. 健康检查
echo "12. 健康检查"
echo "curl ${BASE_URL}/health"
echo ""

echo "=== 示例完成 ==="
