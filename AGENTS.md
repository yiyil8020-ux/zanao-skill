# AGENTS.md

## 环境

- 无 CI、无 linter、无 test suite。唯一验证：`python3 -m py_compile *.py`
- 依赖：`pip install requests mcp`（mcp 是 MCP server 必需）
- `config.json` 在 `.gitignore`，不可提交。`config.example.json` 是模板

## 文件职责

| 文件 | 角色 |
|---|---|
| `SKILL.md` | Agent 指令（**权威入口**） |
| `README.md` | 用户文档（安装/使用/token 获取） |
| `client.py` | 签名 + API 封装 + ZanaoClient |
| `cli.py` | CLI 14 子命令 |
| `mcp_server.py` | FastMCP server（13 tool） |
| `token_tools.py` | token 一键刷新（跨平台） |
| `zanao_*.py` | 薄入口（sys.path 加当前目录后 import） |

## 运行约定

- **优先 MCP**（需配 mcpServers），不可用时必须按 SKILL.md 排查后再降级 CLI
- `config.json` 保存在本目录，不在外部项目。路径逻辑：`client.py` 里 `SKILL_DIR = Path(__file__).resolve().parent`
- 入口脚本不依赖外部目录结构，`sys.path.insert(0, os.path.dirname(__file__))` 自包含

## 跨平台必读

- `cli.py` 和 `token_tools.py` 顶部都有 UTF-8 强制编码（Windows 默认 GBK 不支持 emoji）
- 代理设置按平台分支：macOS `networksetup`，Windows `winreg` 写 `Internet Settings`，Linux 环境变量
- Windows 需杀 WMPF（`WeChatAppEx.exe`）让小程序重读代理
- MCP JSON 里 `command` 在 Windows 上可能需写 `python` 而非 `python3`（后者常指向 Store 空壳）
- `token_tools.py` 启动 mitmweb 前会 socket 探测 8080 端口，被占则先杀旧进程

## token 刷新流程

`token_tools.py` 只依赖 mitmproxy 已装 + 证书已信任。流程：启动代理 → 设系统代理 → 用户手动刷微信 → 自动抓 token 填 `config.json` → 清理。`input()` 有 EOFError 保护（非交互环境自动继续）。清理不在 `finally` 中，只在成功/超时分支显式调用。

## 不可妥协的约束

- `config.json` 含真实凭证，**不可 `git add`**
- 硬编码常量 `SIGN_SALT` / `APP_ID` 来自逆向 wxapkg，服务端更换则全部失效，需重新逆向提取
- 修改 `client.py` 的 `build_headers` 时签名输入是 `alias_nonce_td_盐`，td 秒非毫秒，nonce 20 位数字字符串
