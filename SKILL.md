---
name: zanao
description: |
  赞哦校园集市模块 — 通用版，适配任意高校。
  首次使用引导学校选择 + token 获取。依赖: pip install requests mcp
  触发场景: 浏览帖子/搜索/评论/配图/点赞/发帖/回帖/消息/token 刷新
触发词: 赞哦, 校园集市, 集市, 帖子, 热门, 搭子, zanao
---

# 赞哦校园集市 (通用)

> 🌐 通用版。Config 保存在本目录 `config.json`，不依赖外部项目。

## 调用优先级

1. **优先 MCP** — 如果 agent 有 MCP 能力，用 MCP tool
2. **MCP 故障降级 CLI** — 切到 `python3 ~/.agents/skills/zanao/zanao_client.py <cmd>`
3. **诊断/刷新强制 CLI**

## 初始化（首次使用）

```
1. 检查本目录有无 config.json 且 zanao_token 非空 → 有则跳到第 5 步

2. 询问用户：你在哪个学校的赞哦？请输入学校缩写
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

## 抓 token（手动）

```bash
brew install mitmproxy
mitmweb --no-web-open-browser
open ~/.mitmproxy/mitmproxy-ca-cert.pem  # 钥匙串 → 始终信任
networksetup -setwebproxy Wi-Fi 127.0.0.1 8080
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8080
# 电脑微信 → 赞哦小程序 → 刷一下
# mitmweb http://127.0.0.1:8081 → api.x.zanao.com → X-Sc-Od → 填到 config.json
# 关代理: networksetup -setwebproxystate Wi-Fi off; networksetup -setsecurewebproxystate Wi-Fi off
# pkill -f mitmweb
```

## 换学校

改本目录 config.json 的 `zanao_alias` → 重新抓 token
