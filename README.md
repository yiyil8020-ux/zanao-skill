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

```bash
python3 ~/.agents/skills/zanao/zanao_refresh_token.py  # 全自动刷新
```

## 更多学校

赞噢支持的高校列表见平台小程序。已知可用的学校包括但不限于各地区高校，别名通常为学校英文缩写。

## 许可

MIT
