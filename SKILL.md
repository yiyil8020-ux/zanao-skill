---
name: zanao
description: |
  赞噢校园集市模块 — 通用版，适配任意高校。
  首次使用引导学校选择 + token 获取。依赖: pip install requests mcp
  触发场景: 浏览帖子/搜索/评论/配图/点赞/发帖/回帖/消息/token 刷新
触发词: 赞噢, 校园集市, 集市, 帖子, 热门, 搭子, zanao
---

# 赞噢校园集市 (通用)

> 🌐 通用版。Config 保存在本目录 `config.json`，不依赖外部项目。

## 调用优先级

**MCP 需要手动配一次（贴一段 JSON 到配置文件，重启 agent），配完后自动生效。未配时走 CLI。**

### 启用 MCP（配一次）

把以下 JSON 加到对应 agent 的 mcpServers 配置中。`command` 在 Windows 上写 `python`，macOS/Linux 上写 `python3`：

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

配置位置：你是一个 agent，知道自己的配置文件在哪里。搜索 `{你的运行时名称} mcp server 配置` 即可找到 mcpServers 段的写入位置。如找不到或不确定 → 直接走 CLI（不需要配 MCP 也能用）。

配完重启 agent，MCP tool 即可用。如不确定配没配上，agent 加载 skill 后应自动检测 MCP tool 是否可用。

### 运行时判断（agent 必须遵守）

```
Agent 加载本 skill 后：
  1. 检查自己的可用 tool 列表中有没有 zanao 前缀的 MCP tool
     → 有 → 优先用 MCP tool（hot / list_posts / search_posts 等）
     → 没有 → 告诉用户"需要配置 MCP，见下方说明"，当前降级 CLI

  2. 写操作注意：MCP tool 无确认机制，调用前需向用户复述操作
     CLI 写操作自带 --yes 确认，推荐写操作用 CLI

  3. 诊断和 token 刷新强制 CLI：
     health → python3 ~/.agents/skills/zanao/zanao_client.py health
     token 刷新 → python3 ~/.agents/skills/zanao/zanao_refresh_token.py
```

## 初始化（首次使用）

```
1. 检查本目录有无 config.json 且 zanao_token 非空 → 有则跳到第 5 步

2. 询问用户：你在哪个学校的赞噢？请输入学校缩写
   常见值为学校英文缩写（如 scu, zzu 等），不确定就抓包看 X-Sc-Alias

3. 从 config.example.json 复制为 config.json，写入 alias

4. 获取 token：python3 ~/.agents/skills/zanao/zanao_refresh_token.py
   或者手动抓包（见下方）

5. 验证：python3 ~/.agents/skills/zanao/zanao_client.py health → 全绿即完成
```

## CLI 命令

**读**：`health` · `hot --images` · `list --images` · `search 关键词 --images --history --range 7d` · `comments <tid>` · `user` · `categories` · `messages`

**写（需 `--yes`）**：`like <tid> --yes` · `unlike <tid> --yes` · `post --title ... --content ... --cate-id ... --yes` · `reply <tid> --content ... --yes` · `del-comment <tid> <cid> --yes` · `done <tid> --yes`

## token 刷新

```bash
python3 ~/.agents/skills/zanao/zanao_refresh_token.py  # 全自动
```

## 抓 token（手动，初次设置用）

```
1. 装 mitmproxy: brew install mitmproxy（Windows 用 Fiddler）

2. 启动代理: mitmweb --no-web-open-browser
   首次启动生成证书 ~/.mitmproxy/mitmproxy-ca-cert.pem

3. 信任证书:
   macOS: open ~/.mitmproxy/mitmproxy-ca-cert.pem → 钥匙串 → 始终信任
   Windows: 双击 .p12 → 受信任的根证书颁发机构

4. 设系统代理:
   macOS: networksetup -setwebproxy Wi-Fi 127.0.0.1 8080
          networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8080
   手机: 连同一 Wi-Fi，代理设电脑 IP + 8080，浏览器访问 http://mitm.it 装证书

5. 微信打开赞噢小程序 → 登录 → 刷一下首页

6. 浏览器打开 http://127.0.0.1:8081 → 找 api.x.zanao.com 的请求
   → Request Headers → 复制 X-Sc-Od（token）和 X-Sc-Alias（学校缩写）

7. 写入 ~/.agents/skills/zanao/config.json:
   {"zanao_alias": "学校缩写", "zanao_token": "复制的token"}

8. 关代理: networksetup -setwebproxystate Wi-Fi off
           networksetup -setsecurewebproxystate Wi-Fi off
           pkill -f mitmweb

9. 验证: python3 ~/.agents/skills/zanao/zanao_client.py health → 全绿完成
```

## 换学校

改本目录 config.json 的 `zanao_alias` → 重新抓 token
