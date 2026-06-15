# DiskWise

DiskWise 是一个本地优先的智能文件整理桌面应用。项目计划使用规则、SQLite
和可切换的 AI 模型，为用户生成文件分类、重命名、搜索与整理建议。

当前版本是 **0.1.0 可运行骨架**：

- 可以启动 PySide6 桌面窗口。
- 可以初始化 SQLite 配置数据库。
- 可以检测 Ollama 并列出本机安装的多个模型。
- 可以为分类、命名、视觉和语义搜索分别保存模型选择。
- 可以配置 OpenAI 兼容的云端 API，但云端默认关闭。
- 不会扫描、移动、重命名或删除真实文件。

## 环境要求

- Windows 10/11
- Python 3.12
- 可选：Ollama 与任意兼容模型
- 推荐 IDE：Visual Studio Code

## 安装

```powershell
cd D:\DiskWise
C:\Python\Python312\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## 运行

```powershell
.\.venv\Scripts\diskwise.exe
```

也可以运行：

```powershell
.\.venv\Scripts\python.exe -m diskwise.main
```

## 本地模型

DiskWise 不把模型名称写死在代码中。设置页面会通过 Ollama 本地 API
读取已安装模型：

```text
http://localhost:11434
```

当前默认文本模型是 `gemma4:e2b`，用户可以为不同任务选择其他本地模型。

## 云端 API

云端模式仅支持 OpenAI 兼容协议，并且默认关闭。请复制 `.env.example`
中的变量到自己的环境中。真实密钥不得写入仓库、SQLite 或日志。

DiskWise 不会在本地模型失败时自动改用云端模型。任何云端发送都必须由用户
显式启用，并通过隐私策略检查。

## 运行数据

正式运行时，数据库、缓存、向量索引和日志默认位于：

```text
%LOCALAPPDATA%\DiskWise
```

项目中的 `data/` 仅用于说明开发期目录结构，真实运行数据不会提交 GitHub。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q src tests
```

更多说明见 [docs/architecture.md](docs/architecture.md)。

