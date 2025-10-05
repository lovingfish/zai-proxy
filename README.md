# blackbox-reverse API

blackbox 服务逆向接口，接口适配openai chat api。它使用 FastAPI 构建，可以作为独立应用程序、Docker 容器部署。

## 功能特点

- 兼容 OpenAI API 格式的聊天完成 API 端点
- 支持流式和非流式响应选项
- 支持跨源资源共享（CORS）
- 提供日志记录，便于调试和监控
- 支持 `gpt-4o`,`gemini-1.5-pro-latest`,`claude-3-5-sonnet` 模型

## 设置和安装

1. 克隆仓库

2. 安装依赖：

   ```sh
   pip install -r requirements.txt
   ```

3. 设置环境变量：
   - 在根目录创建 `.env` 文件
   - 添加你的 APP_SECRET：`APP_SECRET=你的密钥`
4. 运行 API：

   ```sh
   python api/main.py
   ```

## 构建

你可以使用 `build.py` 脚本为你的平台构建独立可执行文件：

  ```sh
  python build.py
  ```

这将在 `dist` 目录中创建一个名为 `blackboxai2api` 的可执行文件。

## Docker

构建和运行 Docker 容器：

  ```sh
  docker build -t blackboxai2api .
  docker run -d --name blackboxai2api --restart always -p 8001:8001 -e APP_SECRET=你的密钥 blackboxai2api
  ```

## 使用方法

向 `/v1/chat/completions` 发送 POST 请求，请求体中包含聊天消息和模型规格的 JSON。在 Authorization 头中包含你的 `Bearer APP_SECRET`。
示例：

```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "你好，你好吗？"}
  ],
  "stream": false
}
```

## 支持的模型

目前，API 支持以下模型：

- gpt-4o
- gemini-1.5-pro-latest
- gemini-1.5-pro
- gemini-pro
- claude-3-5-sonnet-20240620
- claude-3-5-sonnet

## 安全性

此 API 使用 APP_SECRET 进行身份验证。确保保管好你的 APP_SECRET，不要在客户端代码中暴露它。

## docker 上传

```bash
docker build -t bbapi . 
docker tag bbapi:latest hpyp/bbapi:latest 
docker push hpyp/bbapi:latest  
```

```bash
docker buildx build --platform linux/arm64 -t bbapi-arm64 .
docker tag bbapi-arm64:latest hpyp/bbapi-arm64:latest
docker push hpyp/bbapi-arm64:latest
```
