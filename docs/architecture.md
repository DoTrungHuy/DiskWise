# DiskWise 架构

DiskWise 使用模块化单体架构。界面、数据库、扫描、搜索、AI Provider、安全策略和文件执行服务都在同一个 Python 桌面应用中，通过清晰接口分离职责。

```text
PySide6 UI
    |
Application services
    |-- Scanner + Extractors
    |-- SQLite repositories
    |-- Rules classifier
    |-- Search services
    |     |-- Keyword search
    |     `-- Semantic vector search
    |-- AI service
    |     |-- Ollama provider
    |     `-- OpenAI-compatible provider
    |-- Planner
    |-- Safety policies
    `-- Confirmed file executor
```

## 当前能力

- 桌面界面包含扫描、搜索、计划、设置四个页面。
- 扫描页可以在用户选择目录后只读遍历文件，并写入 SQLite。
- 规则分类器会根据扩展名识别安装包、视频、图片、文档、压缩包等基础类别。
- 内容提取器只保存短摘要，文本类文件可直接读取；PDF、Word、Excel、图片依赖可选库。
- 搜索服务支持关键词搜索；语义搜索接口已经保留向量存储和相似度计算。
- 重复检测支持大小初筛、快速哈希和完整 SHA-256 哈希。
- 计划服务可以生成按分类整理的移动预览，写入 `plans` 和 `plan_items`。
- 文件执行器支持移动、重命名、跨盘复制校验、回收站删除和撤销入口，但每次都必须显式确认。

## AI Provider

业务代码只依赖 `AIProvider` 接口：

```text
health_check
list_models
generate
embed
```

Ollama Provider 自动读取本机模型，不局限于 Gemma。云端 Provider 使用 OpenAI 兼容协议，并且不会作为本地失败时的自动回退。
