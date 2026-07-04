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

> ⚠️ **MCP 是首选方式，CLI 是最后兜底。不要跳过下面两步直接走 CLI。**

### 第一步：安装依赖（必须先做）

```bash
pip install requests mcp mitmproxy
# Windows 网络慢？用国内镜像：
pip install requests mcp mitmproxy -i https://pypi.tuna.tsinghua.edu.cn/simple
```

没有这一步，MCP server 无法启动，所有 MCP tool 不可用。

### 第二步：配置 mcpServers（必须先做）

把以下 JSON 加到当前 agent 的 mcpServers 配置段。`command` 在 Windows 上写 `python`，macOS/Linux 上写 `python3`：

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

找配置位置：搜索 `{你的运行时名称} mcp server 配置`。

<!-- 注意：Windows 上 python3 可能指向 Store 空壳（exit 49），可改用 python 或用 .venv 的完整路径 -->

配完重启 agent。重启后**验证** MCP tool 已出现在可用 tool 列表中（搜索 `zanao`）。

### 第三步：运行时判断（完成前两步后）

```
1. 确认 MCP tool 可用 → 始终用 MCP（hot / list_posts / search_posts 等）

2. MCP 不可用时的排查顺序（不要直接降级 CLI）：
   a. mcp 包装了没？ → pip install mcp
   b. mcpServers 配了没？ → 检查配置文件
   c. 重启 agent 了吗？ → 重启

3. 排查后仍不可用 → 降级 CLI，但必须告知用户"当前走 CLI"
   诊断 / token 刷新 → 强制 CLI（不走 MCP）
```

## 初始化（首次使用）

> ⚠️ **必须先完成上面第一步（安装依赖）再进行初始化！否则 MCP 和脚本都无法运行。**

```
1. 检查本目录有无 config.json 且 zanao_token 非空 → 有则跳到第 5 步

2. 询问用户：你在哪个学校的赞噢？请输入学校缩写（如 scu, zzu 等）
   → 用户知道 → 写入 alias
   → 用户不知道/不确定 → 先留空 alias，直接跑第 4 步自动抓（zanao_refresh_token.py 会同时抓到 alias 和 token）

3. 从 config.example.json 复制为 config.json，写入 alias（或留空）

4. 获取 token：python3 ~/.agents/skills/zanao/zanao_refresh_token.py
   或者手动抓包（见下方）

5. 验证：python3 ~/.agents/skills/zanao/zanao_client.py health → 全绿即完成

6. 如果配了 MCP，验证 MCP 是否可用：
   重启 agent → 检查 tool 列表有 zanao_ 前缀的 tool → 有则 MCP 生效
   如果没有，说明 mcp 包没装或配置路径不对，当前降级 CLI
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
1. 装 mitmproxy: brew install mitmproxy（macOS）/ pip install mitmproxy（Windows/Linux）

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
