# DevConvert

GitHub: https://github.com/mjydear/devConvert

DevConvert 是一个面向后端与 Agent 开发者的轻量效率工具箱。它把日常开发中的“复制、解析、转换”工作集中到一个网页里：输入一段请求、JSON、日志或对话记录，即可得到可以直接使用的代码、类型定义、错误摘要或评测数据集。

## 工具

- **cURL Request Converter**：将 cURL 转换为 Fetch、Axios、Python requests 和 Java HttpClient 代码；自动脱敏 Authorization、Cookie、Token 等敏感请求头。
- **JSON Type Generator**：将 JSON 转换为 TypeScript interface 和 JSON Schema，适合快速定义后端接口响应类型。
- **Log & Stack Trace Analyzer**：识别日志级别、时间、异常类型与堆栈行号，并按错误签名聚合重复问题。
- **Agent JSONL Dataset Builder**：将 `user/assistant/tool` 对话整理为 JSONL 评测样本，便于构建 Agent 回归测试集。

## 技术栈

- Python 3.10+
- FastAPI + Pydantic
- 原生 HTML/CSS/JavaScript 前端，无需复杂构建链
- pytest + FastAPI TestClient

## 本地运行

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

打开 <http://127.0.0.1:8000>。API 文档位于 <http://127.0.0.1:8000/docs>。

运行测试：

```bash
python -m pytest -q
```

## Windows EXE

在 Windows 上运行仓库中的 `build.ps1`，脚本会安装 PyInstaller 并生成 `dist/DevConvert.exe`。用户无需安装 Python，双击 exe 后会自动启动本地服务并打开浏览器。

```powershell
.\build.ps1
```

打包产物默认不会提交到 GitHub（`dist/` 已加入忽略规则）。可以将 exe 上传到 GitHub Releases，方便其他人下载。

## API 概览

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| POST | `/api/convert/curl` | cURL 请求转换 |
| POST | `/api/convert/json-types` | JSON 类型与 Schema 生成 |
| POST | `/api/analyze/logs` | 日志及异常堆栈分析 |
| POST | `/api/convert/agent-jsonl` | Agent 对话转 JSONL |

请求和响应模型可直接在 FastAPI Swagger 页面查看。所有转换均为无状态操作，不会持久化用户输入。

## 演示与截图

仓库首页建议放置一张工具总览截图，例如 `docs/overview.png`，并为每个工具补充一张操作截图。也可以录制 30 秒 GIF：输入 cURL → 查看生成代码、粘贴日志 → 查看错误聚合、导出 Agent JSONL。当前前端页面可直接作为 GitHub README 的演示入口。

## 简历描述

> 独立开发 DevConvert 开发者效率工具箱，基于 FastAPI 实现 cURL 多语言代码生成、JSON TypeScript/Schema 转换、日志异常聚合与 Agent 对话 JSONL 数据集构建；加入敏感信息脱敏、结构化错误响应和自动化 API 测试，提供可运行的 GitHub 开源项目。

## License

MIT
