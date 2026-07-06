---
name: zanao
description: |
  赞噢校园集市模块 — 通用版，适配任意高校。
  CLI 为主（14 命令），MCP 可选（13 tool）。依赖: pip install requests mcp
 触发场景: 浏览帖子/搜索/评论/配图/点赞/发帖/回帖/消息/token 刷新
触发词: 赞噢, 校园集市, 集市, 帖子, 热门, 搭子, zanao
---

# 赞噢校园集市 (通用)

> 🌐 通用版。Config 保存在本目录 `config.json`，不依赖外部项目。

## 调用方式

**默认用 CLI**（任何 agent 都能跑），MCP 可选（需要额外配置 mcp 包 + agent mcpServers）。

```bash
# CLI — 开箱即用
python3 ~/.agents/skills/zanao/zanao_client.py health
python3 ~/.agents/skills/zanao/zanao_client.py hot
```

### MCP（可选）

MCP 需要手动配一次：

1. 安装依赖：`pip install mcp`
2. 把以下 JSON 加到 agent 的 mcpServers 配置中：

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

配完重启 agent。如不确定配置位置或配不成功 → 直接走 CLI（不需要 MCP 也能用）。

写操作推荐走 CLI（自带 `--yes` 确认），MCP tool 无确认机制。诊断和 token 刷新强制走 CLI。

## 初始化（首次使用）

```
1. 检查本目录有无 config.json 且 zanao_token 非空 → 有则跳到第 4 步

2. 获取 token（二选一）：
   a. python3 ~/.agents/skills/zanao/zanao_refresh_token.py  # 全自动，alias 和 token 一起抓
   b. 手动抓包（见下方）

3. 验证：python3 ~/.agents/skills/zanao/zanao_client.py health → 全绿即完成
```

> 学校缩写（alias）不需要手动填。一键刷新脚本会从请求头 `X-Sc-Alias` 自动获取；手动抓包时 `X-Sc-Alias` 和 `X-Sc-Od` 在同一个请求里，一起复制。

## CLI 命令

**读**：`health` · `hot --images` · `list --images` · `search 关键词 --images --history --range 7d` · `comments <tid>` · `user` · `categories` · `messages`

**写（需 `--yes`）**：`like <tid> --yes` · `unlike <tid> --yes` · `post --title ... --content ... --cate-id ... --yes` · `reply <tid> --content ... --yes` · `del-comment <tid> <cid> --yes` · `done <tid> --yes`

## MCP（13 tool）

`hot` `list_posts` `search_posts` `get_comments` `get_user_info` `get_categories` `get_messages` `like_post` `unlike_post` `post_comment` `delete_comment` `create_post` `change_post_status`

## token 刷新

```bash
python3 ~/.agents/skills/zanao/zanao_refresh_token.py  # 全自动
```

## 抓 token（手动，初次设置用）

```
1. 装 mitmproxy: brew install mitmproxy（macOS）/ pip install mitmproxy（Windows/Linux）

2. 启动代理: mitmweb --no-web-open-browser
   首次启动生成证书 ~/.mitmproxy/mitmproxy-ca-cert.pem

3. 信任证书:
   macOS: open ~/.mitmproxy/mitmproxy-ca-cert.pem → 钥匙串 → 始终信任
   Windows: certutil -addstore Root %USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.cer

4. 设系统代理:
   macOS: networksetup -setwebproxy Wi-Fi 127.0.0.1 8080
          networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8080

5. 微信打开赞噢小程序 → 登录 → 刷一下首页

6. 浏览器打开 http://127.0.0.1:8081 → 找 api.x.zanao.com 的请求
   → Request Headers → 复制 X-Sc-Od（token）和 X-Sc-Alias（学校缩写）

7. 写入 ~/.agents/skills/zanao/config.json:
   {"zanao_alias": "学校缩写", "zanao_token": "复制的token"}

8. 关代理 + 停 mitmweb

9. 验证: python3 ~/.agents/skills/zanao/zanao_client.py health → 全绿完成
```

## 换学校

改本目录 config.json 的 `zanao_alias` → 重新抓 token
