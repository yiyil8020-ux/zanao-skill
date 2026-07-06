"""赞哦 MCP Server（复用 client.py）。"""

import os
from client import ZanaoClient, load_config
from mcp.server.fastmcp import FastMCP


def _get_creds():
    cfg = load_config()
    token = (os.environ.get("ZANAO_TOKEN") or cfg.get("zanao_token") or "").strip()
    alias = (os.environ.get("ZANAO_ALIAS") or cfg.get("zanao_alias") or "lzu").strip() or "lzu"
    if not token:
        raise RuntimeError("缺 ZANAO_TOKEN（设环境变量或填 config.json）")
    return token, alias


mcp = FastMCP("zanao", instructions="赞哦校园集市 MCP。13 个 tool（7 读 + 6 写）。写操作需谨慎使用。")


@mcp.tool()
def hot() -> list[dict]:
    """获取赞哦校园集市热门帖子（最多 10 条）。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).hot()


@mcp.tool()
def list_posts(from_time: str = "0") -> list[dict]:
    """获取最新帖子列表。from_time 起始时间戳，0=最新。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).list(from_time)


@mcp.tool()
def search_posts(keyword: str, page: int = 1, history: bool = False, range_time: str = "") -> list[dict]:
    """搜索帖子。history=False 实时，history=True 历史 (range_time: 1d/3d/7d/1m/6m/1y)。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).search(keyword, page=page, history=history, range_time=range_time or None)


@mcp.tool()
def get_comments(thread_id: str) -> list[dict]:
    """获取帖子的评论列表（含楼中楼回复 reply_list）。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).comments(thread_id)


@mcp.tool()
def get_user_info() -> dict:
    """获取当前登录用户信息。返回 school_name/nickname/user_level_title。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).user_info() or {}


@mcp.tool()
def get_categories() -> list[dict]:
    """获取帖子分类列表。每条含 cate_id/name/summary。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).categories()


@mcp.tool()
def get_messages(from_time: str = "0") -> list[dict]:
    """获取用户消息列表。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).get_messages(from_time)


# === 写操作（需谨慎使用） ===


@mcp.tool()
def like_post(thread_id: str) -> bool:
    """点赞帖子。⚠️ 写操作。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).like_post(thread_id)


@mcp.tool()
def unlike_post(thread_id: str) -> bool:
    """取消点赞帖子。⚠️ 写操作。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).unlike_post(thread_id)


@mcp.tool()
def post_comment(thread_id: str, content: str, reply_comment_id: str = "0", root_comment_id: str = "0", use_anon: int = 0) -> bool:
    """发表评论。⚠️ 写操作。use_anon=1 表示匿名。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).post_comment(thread_id, content, reply_comment_id, root_comment_id, use_anon)


@mcp.tool()
def delete_comment(thread_id: str, comment_id: str) -> bool:
    """删除评论。⚠️ 写操作。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).delete_comment(thread_id, comment_id)


@mcp.tool()
def create_post(title: str, content: str, cate_id: str, img_paths: str = "",
                contact_person: str = "", contact_phone: str = "",
                contact_qq: str = "", contact_wx: str = "") -> bool:
    """发帖。⚠️ 写操作。cate_id 从 get_categories 获取。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).create_post(
        title, content, cate_id, img_paths,
        contact_person, contact_phone, contact_qq, contact_wx,
    )


@mcp.tool()
def change_post_status(thread_id: str, action: str = "finish") -> bool:
    """标记帖子已完成。⚠️ 写操作。action=finish 会隐藏发帖人信息。"""
    token, alias = _get_creds()
    return ZanaoClient(token, alias).change_post_status(thread_id, action)


def run():
    mcp.run()


if __name__ == "__main__":
    run()
