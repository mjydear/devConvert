# DevConvert

> 一个面向后端与 Agent 开发者的轻量工具箱：把请求、数据、日志和对话记录，转换成下一步可以直接使用的结果。

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)
![Tests](https://img.shields.io/badge/tests-9%20passed-2ea44f)
![License](https://img.shields.io/badge/license-MIT-black)

DevConvert 解决的是开发过程中反复出现的几个小问题：从 cURL 生成请求代码、从 JSON 生成类型定义、从日志里找出异常、把 Agent 对话整理成评测数据。所有处理默认在本地完成，不需要登录，也不会持久化输入内容。

## 快速开始

### 直接下载 Windows 版本

不需要安装 Python，下载后双击即可：

[下载 DevConvert.exe](https://github.com/mjydear/devConvert/raw/main/dist/DevConvert.exe)

程序会启动本地服务并自动打开浏览器。首次运行如果遇到 Windows SmartScreen 提示，请确认文件来源后选择“仍要运行”。

### 从源码运行

```bash
git clone https://github.com/mjydear/devConvert.git
cd devConvert

python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

打开 <http://127.0.0.1:8000>。API 调试页面位于 <http://127.0.0.1:8000/docs>。

## 四个工具

| 工具 | 输入 | 输出 | 适用场景 |
| --- | --- | --- | --- |
| **cURL Request Converter** | cURL 命令 | Fetch、Axios、Python、Java 代码 | 调试接口、补充 SDK 示例、快速复现请求 |
| **JSON Type Generator** | JSON 对象或数组 | TypeScript interface、JSON Schema | 对接后端接口、生成响应类型、编写 Mock |
| **Log & Stack Trace Analyzer** | 日志或异常堆栈 | 错误级别、异常摘要、堆栈位置、错误聚合 | 排查线上问题、定位重复异常 |
| **Agent JSONL Dataset Builder** | Agent 对话记录 | JSONL 评测样本 | 整理 Prompt、Response、Tool Call，构建回归测试集 |

### 1. cURL Request Converter

粘贴一段真实接口请求，选择目标语言即可生成代码。转换过程中默认隐藏 `Authorization`、`Cookie` 和 Token，避免把敏感信息直接复制到代码或工单中。

### 2. JSON Type Generator

输入接口响应 JSON，快速得到 TypeScript 类型和 JSON Schema。支持嵌套对象、数组、可选字段和特殊字段名。

### 3. Log & Stack Trace Analyzer

粘贴日志或上传 `.log` / `.txt` 文件，工具会提取时间、级别、异常类型和堆栈行号，并按错误签名聚合，帮助快速判断“发生了什么”和“在哪里发生”。

### 4. Agent JSONL Dataset Builder

支持 `user`、`assistant`、`tool` 对话格式，将一段调试记录转换成可用于评测的 JSONL 样本，便于后续做 Agent 回归测试和数据整理。

## 技术实现

```text
Browser
   |
   v
FastAPI API
   |
   +-- curl_converter.py   cURL 解析与多语言代码生成
   +-- json_types.py       JSON 递归推导与 Schema 生成
   +-- log_analyzer.py     日志正则解析与错误聚合
   +-- agent_jsonl.py      对话归一化与 JSONL 导出
```

- 后端：Python、FastAPI、Pydantic
- 前端：原生 HTML / CSS / JavaScript，无构建链依赖
- 测试：pytest、FastAPI TestClient
- 打包：PyInstaller 单文件 Windows executable
- 数据处理：无状态请求，默认不写入用户输入

## API

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| `GET` | `/health` | 服务健康检查 |
| `POST` | `/api/convert/curl` | cURL 转多语言代码 |
| `POST` | `/api/convert/json-types` | JSON 转 TypeScript / JSON Schema |
| `POST` | `/api/analyze/logs` | 日志与异常堆栈分析 |
| `POST` | `/api/convert/agent-jsonl` | 对话转 JSONL 评测数据 |

完整请求模型和响应示例可在 `/docs` 查看。

## 测试与打包

运行测试：

```bash
python -m pytest -q
```

构建 Windows exe：

```powershell
.\build.ps1
```

构建结果位于 `dist/DevConvert.exe`。`build.ps1` 会自动安装 PyInstaller，并将前端静态文件一起打进 executable。

## 项目结构

```text
devConvert/
├── app.py                     # FastAPI 应用与 API 路由
├── launcher.py                # exe 启动入口
├── build.ps1                  # Windows 打包脚本
├── static/index.html          # 工具箱前端
├── tool_modules/              # 四个工具的独立实现
├── tests/test_api.py          # API 测试
├── requirements.txt
└── DevConvert.spec            # PyInstaller 配置
```

## 简历描述

> 独立设计并开发 DevConvert 开发者效率工具箱，基于 FastAPI 和原生 JavaScript 实现 cURL 多语言代码生成、JSON 类型推导、日志异常聚合和 Agent JSONL 评测数据构建；支持敏感信息脱敏、结构化错误响应、自动化 API 测试及 Windows 单文件部署。

## License

[MIT](LICENSE)
