# AI Provider

## Ollama

默认地址：

```text
http://localhost:11434
```

设置页面调用 `/api/version` 检查服务，调用 `/api/tags` 获取所有已安装模型。项目不会把本地模型写死为单个 Gemma 版本。

## OpenAI 兼容云端 API

云端 API 默认关闭。需要配置：

```text
DISKWISE_CLOUD_ENABLED=true
DISKWISE_CLOUD_BASE_URL=https://provider.example/v1
DISKWISE_CLOUD_API_KEY=...
```

当前支持常见的 `/models`、`/chat/completions` 和 `/embeddings` 协议。Google、Anthropic 等专用协议后续应通过新的 Provider 实现，而不是修改业务代码。

## 模型路由

DiskWise 采用用户按任务手动选择模型：

- 文件分类：默认本地 Ollama `gemma4:e2b`
- 智能命名：默认本地 Ollama `gemma4:e2b`
- 图片理解：由用户选择视觉模型
- 语义搜索：由用户选择向量模型

本地模型失败只提示用户，不自动回退云端。
