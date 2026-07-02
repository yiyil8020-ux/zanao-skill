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

```bash
# CLI
python3 ~/.agents/skills/zanao/zanao_client.py hot
python3 ~/.agents/skills/zanao/zanao_client.py search 搭子 --images --history --range 7d

# MCP（在 agent 的 opencode.json 里配 mcpServers）
```

## token 获取

token 是赞噢的登录凭证，需要从微信小程序里抓包获取。首次设置后过期了用自动刷新。

### 方式一：自动刷新（推荐，仅 macOS）

证书和工具已装好时，一键刷新：

```bash
python3 ~/.agents/skills/zanao/zanao_refresh_token.py
```

脚本自动完成：启动代理 → 设系统代理 → 等你打开微信刷一下赞噢 → 自动抓 token 填 config → 关代理清理。你只需做一件事——电脑微信打开赞噢小程序刷一下。

### 方式二：手动抓包（初次设置 / 非 macOS）

#### 1. 装抓包工具

```bash
# macOS
brew install mitmproxy

# Windows: 下载 Fiddler Classic 或 Charles
# Linux: pip install mitmproxy
```

#### 2. 启动代理并装证书

```bash
mitmweb --no-web-open浏览器    # 启动代理 (端口 8080)，网页界面 http://127.0.0.1:8081
```

第一次启动会在 `~/.mitmproxy/` 生成证书。安装证书并设为受信任：

**macOS**：
```bash
open ~/.mitmproxy/mitmproxy-ca-cert.pem
# → 钥匙串访问 → 双击 mitmproxy → 信任 → 始终信任
```

**Windows**：双击 `mitmproxy-ca-cert.p12` → 受信任的根证书颁发机构

#### 3. 设系统代理

**macOS**：
```bash
networksetup -setwebproxy Wi-Fi 127.0.0.1 8080
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8080
```

**Windows**：设置 → 网络 → 代理 → 127.0.0.1:8080

**手机抓包**（如果电脑端微信用不了赞噢小程序）：手机连同一 Wi-Fi，代理设为电脑 IP + 8080 端口；手机浏览器访问 `http://mitm.it` 安装证书。

#### 4. 打开赞噢小程序

电脑端微信 → 赞噢小程序 → 登录 → 刷一下首页。手机同理。

#### 5. 复制 token

浏览器打开 `http://127.0.0.1:8081`（mitmweb 网页界面），找到 host 为 `api.x.zanao.com` 的任意一条请求，点击 → Request → Headers → 复制 `X-Sc-Od` 的值。

这就是你的 token。同时在同位置可以看到 `X-Sc-Alias`（学校缩写，如 `lzu`）。

#### 6. 写入配置

把 token 和学校缩写填到 `~/.agents/skills/zanao/config.json`：

```json
{
  "zanao_alias": "你的学校缩写",
  "zanao_token": "刚才复制的 token"
}
```

#### 7. 关闭代理

```bash
# macOS
networksetup -setwebproxystate Wi-Fi off
networksetup -setsecurewebproxystate Wi-Fi off

# 杀代理进程
pkill -f mitmweb
```

#### 8. 验证

```bash
python3 ~/.agents/skills/zanao/zanao_client.py health
# → 全绿则 token 有效，配置完成
```

## 更多学校

赞噢支持的高校列表见平台小程序。已知可用的学校包括但不限于各地区高校，别名通常为学校英文缩写。

## 许可

MIT
