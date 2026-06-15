# AI Provider

## Ollama

默认地址：

```text
http://localhost:11434
```

设置页面调用 `/api/version` 检查服务，调用 `/api/tags` 获取所有已安装模型。
项目不会把本地模型写死为单个 Gemma 版本。

## OpenAI 兼容云端 API

云端 API 默认关闭。需要配置：

```text
DISKWISE_CLOUD_ENABLED=true
DISKWISE_CLOUD_BASE_URL=https://provider.example/v1
DISKWISE_CLOUD_API_KEY=...
```

仅支持常见的 `/models`、`/chat/completions` 和 `/embeddings` 协议。专用厂商
协议应通过新的 Provider 实现，而不是修改业务代码。

## 模型路由

0.1 版本采用用户按任务手动选择，不自动路由，也不自动从本地回退云端。

