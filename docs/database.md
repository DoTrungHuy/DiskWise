# 数据库设计

DiskWise 使用 SQLite。SQLite 不需要单独安装服务器，数据库保存在一个本地文件中。

正式运行数据库默认位于 `%LOCALAPPDATA%\DiskWise\diskwise.db`。项目中的 `data/` 只是开发目录结构示例，真实数据库不会上传 GitHub。

## 核心表

- `schema_versions`：记录数据库结构版本。
- `app_settings`：预留普通应用设置，不保存密钥。
- `task_model_configs`：保存分类、命名、视觉和向量任务使用的 Provider 与模型。
- `scan_roots`：记录用户授权扫描过的根目录。
- `files`：保存文件路径、文件名、扩展名、大小、时间、分类和哈希。
- `extracted_content`：保存短内容摘要，不保存完整文档。
- `file_content_fts`：SQLite FTS5 全文搜索索引。
- `classifications`：保存规则或 AI 分类结果。
- `embeddings`：保存语义搜索向量。
- `plans` / `plan_items`：保存整理计划和每个计划项。
- `operations`：预留真实操作和撤销信息。
- `model_runs`：预留模型调用记录。

API 密钥不得写入 SQLite。云端密钥只从进程环境读取，并由 Pydantic `SecretStr` 包装。
