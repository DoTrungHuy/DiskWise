# DiskWise 架构

DiskWise 使用模块化单体架构。界面、数据库、AI Provider、安全策略和未来的
文件操作模块位于同一个 Python 应用中，但通过清晰接口分离职责。

```text
PySide6 UI
    |
Application services
    |-- SQLite repositories
    |-- AI service
    |     |-- Ollama provider
    |     `-- OpenAI-compatible provider
    |-- Safety policies
    `-- Disabled file executor (0.1)
```

## 当前边界

0.1 版本只验证基础设施：

- 初始化数据库。
- 检测本地或云端模型服务。
- 保存每个任务选择的 Provider 和模型名称。
- 启动桌面界面。

扫描、内容提取、搜索、计划和文件执行模块暂时为空。`FileExecutor` 会明确抛出
异常，确保骨架版本不能修改真实文件。

## AI Provider

业务代码只依赖 `AIProvider` 接口：

```text
health_check
list_models
generate
embed
```

Ollama Provider 自动读取本机模型，不局限于 Gemma。云端 Provider 使用
OpenAI 兼容协议，并且不会作为本地失败时的自动回退。

