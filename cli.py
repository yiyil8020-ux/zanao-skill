"""赞哦 CLI 命令层。"""

import sys
import time

# Windows 控制台默认 GBK 不支持 emoji，强制 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from argparse import ArgumentParser

from client import (
    ZanaoClient, get_creds, img_urls,
    ZanaoError, NetworkError
)


def _fmt_post(p):
    tid = p.get("thread_id", "?")
    nick = p.get("nickname", "?")
    cate = p.get("cate_name", "")
    title = p.get("title", "")
    content = p.get("content", "")
    views = p.get("view_count", "?")
    comments = p.get("c_count", "?")
    likes = p.get("l_count", "?")
    ptime = p.get("post_time", "")
    body = f"{title} {content}".strip()
    if len(body) > 80:
        body = body[:80] + "…"
    imgs = p.get("img_paths", []) or []
    img_tag = f"📷{len(imgs)}图 " if imgs else ""
    return f"[{tid}] [{cate}] {img_tag}{nick}: {body} (浏览{views} 评论{comments} 赞{likes} {ptime})"


def _print_posts(posts, show_images=False):
    for p in posts:
        print(_fmt_post(p))
        if show_images:
            for url in img_urls(p.get("img_paths", []) or []):
                print(f"  📷 {url}")


def _handle_error(action, e):
    if isinstance(e, NetworkError):
        print(f"🌐 网络错误: {e}")
        sys.exit(3)
    elif isinstance(e, ZanaoError):
        print(f"❌ {e}")
        print("（如果怀疑 token 过期，运行 python3 ~/.agents/skills/zanao/zanao_refresh_token.py 刷新）")
        sys.exit(1)
    else:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)


def _make_client():
    token, alias = get_creds()
    return ZanaoClient(token, alias)


# === 子命令 ===

def cmd_hot(args):
    c = _make_client()
    try:
        posts = c.hot()
    except Exception as e:
        _handle_error("获取热门帖子", e)
        return
    if not posts:
        print("⚠️ 没抓到热门帖子")
        sys.exit(1)
    print(f"🔥 热门帖子 — 共 {len(posts)} 条\n")
    _print_posts(posts, getattr(args, "images", False))


def cmd_list(args):
    c = _make_client()
    try:
        posts = c.list(args.from_time)
    except Exception as e:
        _handle_error("获取帖子列表", e)
        return
    print(f"📋 最新帖子 — 共 {len(posts)} 条\n")
    _print_posts(posts, getattr(args, "images", False))


def cmd_search(args):
    c = _make_client()
    try:
        posts = c.search(args.keyword, page=args.page, history=args.history, range_time=args.range)
    except Exception as e:
        _handle_error("搜索帖子", e)
        return
    scope = "历史" if args.history else "实时"
    print(f"🔍 {scope}搜索 '{args.keyword}' — 共 {len(posts)} 条\n")
    _print_posts(posts, getattr(args, "images", False))


def cmd_comments(args):
    c = _make_client()
    try:
        comments = c.comments(args.thread_id)
    except Exception as e:
        _handle_error("获取评论", e)
        return
    print(f"💬 评论 — 共 {len(comments)} 条\n")
    for cm in comments:
        cid = cm.get("comment_id", "?")
        nick = cm.get("nickname", "?")
        content = cm.get("content", "")
        ptime = cm.get("post_time_text", "")
        likes = cm.get("like_num", "?")
        print(f"[{cid}] {nick}: {content} (赞{likes} {ptime})")
        for reply in cm.get("reply_list", []) or []:
            rcid = reply.get("comment_id", "?")
            rnick = reply.get("nickname", "?")
            rcontent = reply.get("content", "")
            rtime = reply.get("post_time_text", "")
            print(f"  └ [{rcid}] {rnick}: {rcontent} ({rtime})")


def cmd_user(args):
    token, alias = get_creds()
    c = ZanaoClient(token, alias)
    try:
        info = c.user_info()
    except Exception as e:
        _handle_error("获取用户信息", e)
        return
    if not isinstance(info, dict):
        print(f"⚠️ 响应结构异常")
        sys.exit(1)
    school = info.get("school_name", "?")
    ui = info.get("user_info", {}) or {}
    nick = ui.get("nickname", "?")
    level = ui.get("user_level_title", "?")
    print(f"👤 {nick} (等级:{level}) @ {school}")
    print(f"   alias: {alias}")
    print(f"   token 末4位: ...{token[-4:] if len(token) >= 4 else token}")


def cmd_categories(args):
    c = _make_client()
    try:
        cats = c.categories()
    except Exception as e:
        _handle_error("获取分类", e)
        return
    print(f"📂 分类 — 共 {len(cats)} 个\n")
    for cat in cats:
        cid = cat.get("cate_id", "?")
        name = cat.get("name", "?")
        summary = cat.get("summary", "")
        print(f"[{cid}] {name}: {summary}")


def cmd_health(args):
    """全面体检：config → token → API → 网络。"""
    from client import load_config

    print("🩺 赞哦 健康检查")
    print("=" * 40)

    # 1. config.json
    cfg = load_config()
    token = cfg.get("zanao_token", "").strip()
    alias = cfg.get("zanao_alias", "lzu").strip() or "lzu"
    if token:
        print(f"✅ config.json: token 已配置 (alias={alias}, 末4位=...{token[-4:]})")
    else:
        print(f"❌ config.json: zanao_token 为空")
        print("   首次配置: 见 README 赞哦章节")
        print("   token 过期: python3 ~/.agents/skills/zanao/zanao_refresh_token.py")
        return

    # 2. API 网络连通性
    import requests
    try:
        r = requests.head("https://api.x.zanao.com", timeout=5)
        print(f"✅ API 连通: HTTP {r.status_code}")
    except Exception:
        print(f"❌ API 不通: 检查网络/VPN")
        return

    # 3. token 验证
    c = ZanaoClient(token, alias)
    ok, info = c.check_token()
    if ok:
        school = info.get("school_name", "?")
        ui = info.get("user_info", {}) or {}
        nick = ui.get("nickname", "?")
        level = ui.get("user_level_title", "?")
        print(f"✅ token 有效: {nick} (等级:{level}) @ {school}")
    else:
        print(f"❌ token 无效: {info}")
        print("   运行 python3 ~/.agents/skills/zanao/zanao_refresh_token.py 刷新")

    # 4. 数据抓取测试
    try:
        posts = c.hot()
        if posts:
            print(f"✅ 数据抓取: 热门帖子 {len(posts)} 条")
        else:
            print(f"⚠️  数据抓取: 返回空（可能无数据）")
    except Exception as e:
        print(f"❌ 数据抓取失败: {e}")

    # 5. mitmproxy 可用性
    import shutil
    if shutil.which("mitmproxy") or shutil.which("mitmweb"):
        print(f"✅ mitmproxy: 已安装")
    else:
        print(f"⚠️  mitmproxy: 未安装（token 刷新需要: brew install mitmproxy）")

    # 6. 证书
    from pathlib import Path as P
    cert = P.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    if cert.exists():
        print(f"✅ mitmproxy 证书: 已生成")
    else:
        print(f"⚠️  mitmproxy 证书: 未生成（需先运行一次 mitmweb）")

    print("=" * 40)


def cmd_like(args):
    """点赞帖子。需要 --yes 确认（写操作）。"""
    if not args.yes:
        a = input(f"确认点赞帖子 {args.thread_id}？(y/N) ")
        if a.strip().lower() != 'y':
            print("已取消")
            return
    c = _make_client()
    try:
        c.like_post(args.thread_id)
        print(f"✅ 已点赞帖子 {args.thread_id}")
    except Exception as e:
        _handle_error("点赞", e)


def cmd_unlike(args):
    """取消点赞帖子。需要 --yes 确认（写操作）。"""
    if not args.yes:
        a = input(f"确认取消点赞帖子 {args.thread_id}？(y/N) ")
        if a.strip().lower() != 'y':
            print("已取消")
            return
    c = _make_client()
    try:
        c.unlike_post(args.thread_id)
        print(f"✅ 已取消点赞帖子 {args.thread_id}")
    except Exception as e:
        _handle_error("取消点赞", e)


def _confirm(msg, args):
    if not getattr(args, "yes", False):
        a = input(f"{msg} (y/N) ")
        if a.strip().lower() != 'y':
            print("已取消")
            return False
    return True


def cmd_post(args):
    if not _confirm(f"确认发帖？标题: {args.title}", args):
        return
    c = _make_client()
    try:
        c.create_post(
            title=args.title,
            content=args.content,
            cate_id=args.cate_id,
            img_paths=args.img_paths or "",
            contact_person=args.contact_person or "",
            contact_phone=args.contact_phone or "",
            contact_qq=args.contact_qq or "",
            contact_wx=args.contact_wx or "",
        )
        print(f"✅ 发帖成功！标题: {args.title}")
    except Exception as e:
        _handle_error("发帖", e)


def cmd_reply(args):
    msg = f"确认回复帖子 {args.thread_id}？内容: {args.content[:50]}"
    if not _confirm(msg, args):
        return
    c = _make_client()
    try:
        c.post_comment(
            thread_id=args.thread_id,
            content=args.content,
            reply_comment_id=getattr(args, "comment_id", None) or "0",
            root_comment_id=getattr(args, "root_id", None) or "0",
            use_anon=1 if getattr(args, "anon", False) else 0,
        )
        print(f"✅ 已回复帖子 {args.thread_id}")
    except Exception as e:
        _handle_error("回复", e)


def cmd_del_comment(args):
    if not _confirm(f"确认删除评论 {args.comment_id}（帖子 {args.thread_id}）？", args):
        return
    c = _make_client()
    try:
        c.delete_comment(args.thread_id, args.comment_id)
        print(f"✅ 已删除评论 {args.comment_id}")
    except Exception as e:
        _handle_error("删除评论", e)


def cmd_done(args):
    if not _confirm(f"确认标记帖子 {args.thread_id} 为已完成（会隐藏发帖人信息）？", args):
        return
    c = _make_client()
    try:
        c.change_post_status(args.thread_id, "finish")
        print(f"✅ 帖子 {args.thread_id} 已标记完成")
    except Exception as e:
        _handle_error("标记完成", e)


def cmd_messages(args):
    c = _make_client()
    try:
        msgs = c.get_messages(args.from_time)
        print(f"📬 消息 — 共 {len(msgs)} 条\n")
        for m in msgs:
            mid = m.get("msg_id", "?")
            mtype = m.get("msg_type", "?")
            mtitle = m.get("msg_title", "")
            ctime = m.get("create_time", "")
            from_u = (m.get("from_user_info") or {}).get("nickname", "?")
            print(f"[{mid}] [{mtype}] {from_u}: {mtitle} ({ctime})")
            thread = m.get("thread_info")
            if isinstance(thread, dict) and thread.get("thread_id"):
                print(f"  → 帖子: {thread.get('thread_id')} {thread.get('title', '')}")
            comment = m.get("comment_info")
            if isinstance(comment, dict) and comment.get("content"):
                print(f"  → 评论: {comment.get('content', '')[:60]}")
    except Exception as e:
        _handle_error("消息", e)


def main():
    ap = ArgumentParser(description="赞哦校园集市 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_hot = sub.add_parser("hot", help="热门帖子")
    p_hot.add_argument("--images", "-i", action="store_true", help="显示配图 URL")
    p_hot.set_defaults(func=cmd_hot)

    p_list = sub.add_parser("list", help="最新帖子")
    p_list.add_argument("--from-time", default="0", help="起始时间戳, 0=最新")
    p_list.add_argument("--images", "-i", action="store_true", help="显示配图 URL")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="搜索帖子")
    p_search.add_argument("keyword", help="关键词")
    p_search.add_argument("--page", type=int, default=1, help="页码")
    p_search.add_argument("--history", action="store_true", help="搜历史帖子")
    p_search.add_argument("--range", default=None, help="时间范围: 1d/3d/7d/1m/6m/1y")
    p_search.add_argument("--images", "-i", action="store_true", help="显示配图 URL")
    p_search.set_defaults(func=cmd_search)

    p_cmt = sub.add_parser("comments", help="帖子评论")
    p_cmt.add_argument("thread_id", help="帖子 ID")
    p_cmt.set_defaults(func=cmd_comments)

    sub.add_parser("user", help="当前用户信息 (验证 token)").set_defaults(func=cmd_user)
    sub.add_parser("categories", help="帖子分类").set_defaults(func=cmd_categories)
    sub.add_parser("health", help="全面体检 (config/token/网络/API)").set_defaults(func=cmd_health)

    p_like = sub.add_parser("like", help="点赞帖子 ⚠️ 写操作")
    p_like.add_argument("thread_id", help="帖子 ID")
    p_like.add_argument("--yes", "-y", action="store_true", help="跳过确认")
    p_like.set_defaults(func=cmd_like)

    p_unlike = sub.add_parser("unlike", help="取消点赞帖子 ⚠️ 写操作")
    p_unlike.add_argument("thread_id", help="帖子 ID")
    p_unlike.add_argument("--yes", "-y", action="store_true", help="跳过确认")
    p_unlike.set_defaults(func=cmd_unlike)

    p_post = sub.add_parser("post", help="发帖 ⚠️ 写操作")
    p_post.add_argument("--title", required=True, help="标题")
    p_post.add_argument("--content", required=True, help="正文")
    p_post.add_argument("--cate-id", required=True, help="分类 ID（先跑 categories 查看）")
    p_post.add_argument("--img-paths", default="", help="图片路径,逗号分隔（需先上传）")
    p_post.add_argument("--contact-person", default="", help="联系人")
    p_post.add_argument("--contact-phone", default="", help="联系电话")
    p_post.add_argument("--contact-qq", default="", help="联系 QQ")
    p_post.add_argument("--contact-wx", default="", help="联系微信")
    p_post.add_argument("--yes", "-y", action="store_true", help="跳过确认")
    p_post.set_defaults(func=cmd_post)

    p_reply = sub.add_parser("reply", help="回复帖子/评论 ⚠️ 写操作")
    p_reply.add_argument("thread_id", help="帖子 ID")
    p_reply.add_argument("--content", required=True, help="回复内容")
    p_reply.add_argument("--comment-id", default=None, help="回复的评论 ID（回复评论时用）")
    p_reply.add_argument("--root-id", default=None, help="根评论 ID（楼中楼时用）")
    p_reply.add_argument("--anon", action="store_true", help="匿名回复")
    p_reply.add_argument("--yes", "-y", action="store_true", help="跳过确认")
    p_reply.set_defaults(func=cmd_reply)

    p_del = sub.add_parser("del-comment", help="删除评论 ⚠️ 写操作")
    p_del.add_argument("thread_id", help="帖子 ID")
    p_del.add_argument("comment_id", help="评论 ID")
    p_del.add_argument("--yes", "-y", action="store_true", help="跳过确认")
    p_del.set_defaults(func=cmd_del_comment)

    p_done = sub.add_parser("done", help="标记帖子已完成 ⚠️ 写操作")
    p_done.add_argument("thread_id", help="帖子 ID")
    p_done.add_argument("--yes", "-y", action="store_true", help="跳过确认")
    p_done.set_defaults(func=cmd_done)

    p_msg = sub.add_parser("messages", help="用户消息列表")
    p_msg.add_argument("--from-time", default="0", help="起始时间戳")
    p_msg.set_defaults(func=cmd_messages)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
