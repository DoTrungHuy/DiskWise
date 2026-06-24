# Web Workbench Prototype

DiskWise 现在保留 PySide6 桌面壳作为稳定入口，同时新增一个本地浏览器工作台原型。这个原型用于验证更完整的文件整理流程：扫描状态、资料库、搜索、重复文件、计划预览、明确确认执行、活动日志和撤销。

## 运行方式

后端只绑定 `127.0.0.1`：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,web]"
.\.venv\Scripts\diskwise-api.exe
```

前端开发服务器：

```powershell
cd web
npm install
npm run dev
```

默认访问地址是 `http://127.0.0.1:5173`，前端会通过 Vite proxy 调用 `http://127.0.0.1:8765/api/*`。

如果只想做本地预览，可以先构建前端，再从 FastAPI 同源访问：

```powershell
cd web
npm run build
cd ..
.\.venv\Scripts\diskwise-api.exe
```

然后打开 `http://127.0.0.1:8765`。当 `web/dist` 存在时，API 会自动挂载构建后的工作台静态文件。

## 信息架构

- Dashboard: 已索引文件数、扫描根目录、分类分布、重复组、最新整理计划、AI Provider 健康状态。
- Library: 分类、搜索过滤、文件状态、选中文件检查器、摘要提取。
- Search: 关键词搜索、重复文件模式、未来语义搜索占位。
- Plans: 移动前后路径、分类理由、风险标记、逐项选择和 `EXECUTE` 确认。
- Activity: 操作日志和可撤销移动的 undo。
- Settings: 各 AI 任务当前模型和云端启用状态。

## 产品参考

- Czkawka: 按问题类型组织清理工具，重复文件以组为中心展示。
- organize: 真实执行前必须先看模拟结果。
- TagStudio: 以资料库覆盖已有文件夹，而不是要求用户重建目录结构。
- File Sense: 把关键词、元数据和未来自然语言搜索拆成清楚的模式。

## 当前边界

- Web shell 是原型，不替换 PySide6。
- 真实文件移动只来自 Plans 的确认执行，Library 和 Search 只读。
- 测试和演示应使用临时目录，不要用用户真实 Downloads 或 Desktop 做冒烟执行。
- Tauri 打包留到流程验证后再做。
