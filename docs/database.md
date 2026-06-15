# 数据库设计

DiskWise 使用 SQLite。SQLite 不需要单独安装服务器，数据库保存在一个本地
文件中。

0.1 版本包含三张表：

- `schema_versions`：记录数据库结构版本。
- `app_settings`：预留普通应用设置，不保存密钥。
- `task_model_configs`：保存分类、命名、视觉和向量任务使用的 Provider 与模型。

正式运行数据库默认位于 `%LOCALAPPDATA%\DiskWise\diskwise.db`。项目中的
`data/` 只是开发目录结构示例。

API 密钥不得写入 SQLite。云端密钥只从进程环境读取，并由 Pydantic
`SecretStr` 包装。

