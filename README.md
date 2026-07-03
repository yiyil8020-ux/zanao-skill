# Zanao Skill

赞噢校园集市 AI Skill — 适配任意高校，开箱即用。

## 快速开始

```bash
# 1. 安装
git clone https://github.com/yiyil8020-ux/zanao-skill.git ~/.agents/skills/zanao
pip install requests mcp

# 2. Agent 加载后自动走初始化：询问学校缩写 → 引导获取 token

# 3. 开始使用
python3 ~/.agents/skills/zanao/zanao_client.py hot          # 热门帖子
python3 ~/.agents/skills/zanao/zanao_client.py health        # 健康检查
```

## 功能

| 功能 | CLI | MCP |
|---|---|---|
| 浏览热门/最新帖子 | ✅ `hot` `list` | ✅ `hot` `list_posts` |
| 搜索帖子 | ✅ `search` 实时+历史 | ✅ `search_posts` |
| 看评论+配图 | ✅ `comments` `--images` | ✅ `get_comments` |
| 点赞/取消赞 | ✅ `like` `unlike` | ✅ `like_post` `unlike_post` |
| 发帖/回帖/删评论 | ✅ `post` `reply` `del-comment` | ✅ `create_post` `post_comment` `delete_comment` |
| 标记帖子完成 | ✅ `done` | ✅ `change_post_status` |
| 消息列表 | ✅ `messages` | ✅ `get_messages` |
| token 一键刷新 | ✅ `zanao_refresh_token.py` | — |
| 健康检查 | ✅ `health` | — |

所有写操作需 `--yes` 确认，防止 agent 误调用。

## 使用

Agent 加载本 skill 后自动走初始化流程：询问学校缩写 → 引导获取 token → 完成。之后直接调用命令。

### CLI（默认，开箱即用）

```bash
python3 ~/.agents/skills/zanao/zanao_client.py hot
python3 ~/.agents/skills/zanao/zanao_client.py search 搭子 --images --history --range 7d
python3 ~/.agents/skills/zanao/zanao_client.py health
```

### MCP（配一次，自动生效）

MCP 需要手动配一次。把以下 JSON 加到对应 agent 的 mcpServers 配置中：

```json
{
  "mcpServers": {
    "zanao": {
      "command": "python3",
      "args": ["~/.agents/skills/zanao/zanao_mcp.py"]
    }
  }
}
```

配置位置：
- **Claude Code**：`~/.claude.json` 的 `mcpServers` 段，或项目根 `.mcp.json`
- **OpenCode**：项目 `.opencode/opencode.json` 或 `~/.config/opencode/opencode.json`
- **Cursor / Cline / Roo Code**：Settings → MCP → 添加 server

配完重启 agent，MCP tool（`hot` / `list_posts` / `search_posts` / `get_comments` / `get_user_info` / `get_categories`）即可用。

> 写操作推荐走 CLI（自带 `--yes` 确认），MCP tool 无确认机制。诊断和 token 刷新强制走 CLI。

## token 获取

token 是赞噢的登录凭证，需要从微信小程序里抓包获取。首次设置后过期了用自动刷新。

### 方式一：自动刷新（推荐）

证书和工具已装好时，一键刷新：

```bash
python3 ~/.agents/skills/zanao/zanao_refresh_token.py
```

脚本自动完成：启动代理 → 设系统代理 → 等你打开微信刷一下赞噢 → 自动抓 token 填 config → 关代理清理。你只需做一件事——电脑微信打开赞噢小程序刷一下。

> 自动刷新依赖 mitmproxy，Windows 也需要 `pip install mitmproxy`。

### 方式二：手动抓包（初次设置时用）

以下步骤每步区分系统。做完这一次，以后过期直接用方式一。

#### 1. 装抓包工具

**macOS / Linux**
```bash
brew install mitmproxy        # macOS
pip install mitmproxy         # Linux
```

**Windows**：下载 [Fiddler Classic](https://www.telerik.com/fiddler/fiddler-classic)，安装后启动，Tools → Options → HTTPS → 勾选 Decrypt HTTPS traffic → 弹窗点 Yes 信任证书。Fiddler 自动接管系统代理，无需手动设。

#### 2. 启动代理并信任证书

**macOS / Linux — mitmproxy**
```bash
mitmweb --no-web-open-browser
```
第一次启动生成证书 `~/.mitmproxy/mitmproxy-ca-cert.pem`。

```bash
# macOS: 导入钥匙串并设信任
open ~/.mitmproxy/mitmproxy-ca-cert.pem
# → 钥匙串 → 双击 mitmproxy → 信任 → 始终信任 → 输密码

# Linux
sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
sudo update-ca-certificates
```

**Windows — Fiddler**：启动 Fiddler 时已自动处理证书和代理，跳过步骤 2 和 3。

#### 3. 设系统代理

**macOS**
```bash
networksetup -setwebproxy Wi-Fi 127.0.0.1 8080
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8080
```

**Windows**：Fiddler 自动接管，无需手动操作。

**Linux**
```bash
export http_proxy=http://127.0.0.1:8080
export https_proxy=http://127.0.0.1:8080
```

**手机抓包**：手机连同一 Wi-Fi，代理设为电脑 IP + 8080 端口；手机浏览器访问 `http://mitm.it` 安装证书。

#### 4. 打开赞噢小程序

电脑端微信 → 赞噢小程序 → 登录 → 刷一下首页。手机同理。

#### 5. 复制 token

- **mitmproxy**：浏览器打开 `http://127.0.0.1:8081`，找 host 为 `api.x.zanao.com` 的请求 → Request Headers → 复制 `X-Sc-Od`
- **Fiddler**：左侧列表找 `api.x.zanao.com` → 右侧 Inspectors → Raw → 找 `X-Sc-Od`

同时在同位置可以看到 `X-Sc-Alias`（学校缩写）。

#### 6. 写入配置

```json
{"zanao_alias": "学校缩写", "zanao_token": "复制的 token"}
```
保存到 `~/.agents/skills/zanao/config.json`。

#### 7. 关闭代理

- **macOS**：`networksetup -setwebproxystate Wi-Fi off && networksetup -setsecurewebproxystate Wi-Fi off`，终端 `Ctrl+C` 停 mitmweb
- **Windows**：关闭 Fiddler（自动还原代理）
- **Linux**：`unset http_proxy https_proxy`，终端 `Ctrl+C` 停 mitmweb

#### 8. 验证

```bash
python3 ~/.agents/skills/zanao/zanao_client.py health
```

全绿则完成。以后 token 过期用方式一。

## 更多学校

赞噢支持的高校列表见平台小程序。已知可用的学校包括但不限于各地区高校，别名通常为学校英文缩写。

## 许可

MIT
