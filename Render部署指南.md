# Render 部署指南

本指南将帮助您在 Render 平台上部署 ZAI Proxy API 服务。

## 前置要求

- 一个 [Render](https://render.com) 账号
- 本项目的 GitHub 仓库（或其他 Git 托管服务）

## 部署步骤

### 1. 准备仓库

确保您的代码已推送到 GitHub、GitLab 或 Bitbucket。

### 2. 创建 Web Service

1. 登录 [Render Dashboard](https://dashboard.render.com/)
2. 点击 **New +** 按钮，选择 **Web Service**
3. 连接您的 Git 仓库
4. 选择包含本项目的仓库

### 3. 配置服务

在服务配置页面，填写以下信息：

#### 基本设置

- **Name**: `zai-proxy`（或您喜欢的名称）
- **Region**: 选择离您用户最近的区域
- **Branch**: `main`（或您的主分支名称）
- **Root Directory**: 留空（如果项目在根目录）
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

#### 环境变量

在 **Environment Variables** 部分添加以下变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `PORT` | `8001` | 服务端口（Render 会自动设置，可选） |
| `HOST` | `0.0.0.0` | 监听地址 |
| `WORKERS` | `1` | Worker 进程数（根据实例大小调整） |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DEBUG` | `False` | 是否开启调试模式 |
| `PROXY_URL` | `https://chat.z.ai` | 代理目标 URL |

**注意**: Render 会自动提供 `PORT` 环境变量，您的应用需要监听该端口。

### 4. 选择实例类型

- **Instance Type**:
  - 免费层：`Free`（适合测试，有使用限制）
  - 付费层：`Starter` 或更高（适合生产环境）

### 5. 部署

1. 点击 **Create Web Service** 按钮
2. Render 将自动开始构建和部署您的应用
3. 等待部署完成（通常需要 2-5 分钟）

### 6. 验证部署

部署完成后，您将获得一个 URL，格式类似：`https://zai-proxy.onrender.com`

测试健康检查端点：
```bash
curl https://your-app-name.onrender.com/health
```

应该返回：
```json
{"status": "ok"}
```

测试主页：
```bash
curl https://your-app-name.onrender.com/
```

应该返回：
```
ZAI Proxy Powered by snaily
```

## 使用 API

### 获取模型列表

```bash
curl https://your-app-name.onrender.com/v1/models
```

### 聊天完成（非流式）

```bash
curl -X POST https://your-app-name.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": false
  }'
```

### 聊天完成（流式）

```bash
curl -X POST https://your-app-name.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "model": "glm-4.6",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": true
  }'
```

## 支持的模型

- `glm-4.6` - GLM-4.6
- `glm-4.5V` - GLM-4.5V（支持视觉）
- `glm-4.5` - GLM-4.5
- `glm-4.6-search` - GLM-4.6 搜索版
- `glm-4.6-advanced-search` - GLM-4.6 高级搜索版
- `glm-4.6-nothinking` - GLM-4.6 无思考链版

## 高级配置

### 自定义域名

1. 在 Render Dashboard 中，进入您的服务
2. 点击 **Settings** 标签
3. 在 **Custom Domain** 部分添加您的域名
4. 按照提示配置 DNS 记录

### 自动部署

Render 默认启用自动部署。每次推送到指定分支时，服务会自动重新部署。

如需禁用：
1. 进入服务的 **Settings**
2. 找到 **Auto-Deploy** 选项
3. 关闭自动部署

### 扩展实例

如需处理更多流量：
1. 进入服务的 **Settings**
2. 在 **Instance Type** 部分选择更高级别的实例
3. 增加 `WORKERS` 环境变量的值（建议：CPU 核心数 × 2 + 1）

### 查看日志

1. 在 Render Dashboard 中进入您的服务
2. 点击 **Logs** 标签查看实时日志
3. 使用搜索功能过滤特定日志

### 健康检查

Render 会自动监控 `/health` 端点。如果健康检查失败，Render 会自动重启服务。

## 注意事项

1. **免费层限制**：
   - 服务在 15 分钟无活动后会休眠
   - 每月有 750 小时的免费使用时间
   - 首次请求可能需要等待服务唤醒（冷启动）

2. **认证**：
   - 所有 API 请求都需要在 `Authorization` 头中提供有效的访问令牌
   - 格式：`Bearer YOUR_ACCESS_TOKEN`

3. **CORS**：
   - 服务已配置允许所有来源的跨域请求
   - 生产环境建议限制允许的来源

4. **日志**：
   - Render 保留最近的日志
   - 建议集成外部日志服务（如 Papertrail）用于长期存储

5. **性能优化**：
   - 使用付费实例以获得更好的性能和稳定性
   - 根据负载调整 `WORKERS` 数量
   - 考虑使用 CDN 缓存静态内容

## 故障排查

### 服务无法启动

1. 检查 **Logs** 中的错误信息
2. 确认 `requirements.txt` 中的依赖都能正确安装
3. 验证 `Start Command` 是否正确

### 502 Bad Gateway

1. 确认应用监听的是 Render 提供的 `$PORT` 环境变量
2. 检查应用是否成功启动
3. 查看日志中是否有错误

### 请求超时

1. 检查上游服务（`https://chat.z.ai`）是否可访问
2. 考虑增加实例规格
3. 优化代码性能

### 认证失败

1. 确认请求头中包含正确的 `Authorization` 字段
2. 验证访问令牌格式：`Bearer YOUR_TOKEN`
3. 检查令牌是否有效

## 成本估算

- **免费层**：$0/月（有限制）
- **Starter**：$7/月起
- **Standard**：$25/月起

详细定价请访问：https://render.com/pricing

## 相关链接

- [Render 官方文档](https://render.com/docs)
- [Render Python 部署指南](https://render.com/docs/deploy-fastapi)
- [项目 GitHub 仓库](https://github.com/your-username/zai-proxy)

## 支持

如遇到问题，请：
1. 查看 Render 日志
2. 检查本文档的故障排查部分
3. 在项目仓库提交 Issue
