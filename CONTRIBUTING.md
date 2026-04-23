# 贡献指南

感谢你考虑为 File Share Cloud 做出贡献！🎉

## 如何贡献

### 报告 Bug

如果你发现了 Bug，请提交 Issue 并包含以下信息：

- 清晰的 Bug 描述
- 重现步骤
- 预期行为 vs 实际行为
- 环境信息（Python 版本、操作系统、Docker 版本等）
- 相关日志或截图

### 请求新功能

我们欢迎新功能请求！请提交 Issue 并描述：

- 你的使用场景
- 期望的功能
- 为什么这个功能对项目有价值

### 代码贡献

1. **Fork 本仓库**

2. **克隆你的 Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-file-share.git
   cd ai-file-share
   ```

3. **创建特性分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **安装开发依赖**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

5. **进行开发**
   - 遵循现有的代码风格
   - 添加测试（如果有）
   - 确保代码通过 linting

6. **提交更改**
   ```bash
   git commit -m "Add: 简要描述你的更改"
   ```

7. **推送到你的 Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

8. **创建 Pull Request**

## 开发环境设置

### 本地运行

```bash
# 克隆项目
git clone https://github.com/intrust/ai-file-share.git
cd ai-file-share

# 进入 server 目录
cd server

# 安装依赖
pip install -r requirements.txt

# 运行服务
python main.py
```

### 使用 Docker

```bash
# 构建镜像
docker build -t file-share-cloud .

# 运行容器
docker run -d -p 8080:8080 \
  -v file-share-data:/data \
  -v file-share-db:/data/db \
  file-share-cloud
```

### 运行测试

```bash
cd server
pytest tests/ -v
```

## 代码规范

- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- 使用 type hints
- 为复杂函数添加 docstring
- 保持函数简短（不超过 50 行）

## Pull Request 指南

- PR 标题要清晰描述所做的更改
- 描述中要解释**为什么**这个更改是必要的
- 附上相关的 Issue 链接
- 确保所有 CI 检查通过

## 行为准则

请尊重所有参与项目的人。我们遵循 [行为准则](CODE_OF_CONDUCT.md)。

## 有问题？

- 📖 查看 [文档](README.md)
- 💬 加入讨论 [GitHub Discussions](https://github.com/intrust/ai-file-share/discussions)
- 🐛 提交 [Bug](https://github.com/intrust/ai-file-share/issues/new?template=bug_report.md)
- ✨ 请求 [功能](https://github.com/intrust/ai-file-share/issues/new?template=feature_request.md)

再次感谢你的贡献！❤️
