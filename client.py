"""赞哦 API 客户端核心。

签名复现自 jeanhua/ZanaoMCP Go 实现，每次请求重新生成 nonce。
内置重试、token 状态检测、详细错误提示。
"""

import hashlib
import json
import random
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

SKILL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SKILL_DIR / "config.json"

API_BASE = "https://api.x.zanao.com"
APP_ID = "wx3921ddb0258ff14f"
SIGN_SALT = "1b6d2514354bc407afdd935f45521a8c"
CLIENT_VERSION = "3.4.4"
CDN_BASE = "https://b1.cdn.zanao.com"
CDN_THUMB = "@!sm_w400"
MAX_RETRIES = 2

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 "
    "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
    "MiniProgramEnv/Windows WindowsWechat/WMPF "
    "WindowsWechat(0x63090c33)XWEB/14185"
)


class ZanaoError(Exception):
    pass


class NetworkError(ZanaoError):
    pass


def load_config():
    if CONFIG_PATH.exists():
        return json.load(open(CONFIG_PATH, encoding="utf-8"))
    return {}


def get_creds(exit_on_missing=True):
    cfg = load_config()
    token = (cfg.get("zanao_token") or "").strip()
    alias = (cfg.get("zanao_alias") or "lzu").strip() or "lzu"
    if not token and exit_on_missing:
        print("ERROR: config.json 没填 zanao_token")
        print("首次配置: 按 README 赞哦章节抓包获取")
        print("token 过期: python3 scripts/zanao_refresh_token.py")
        sys.exit(1)
    return token, alias


def _gen_nonce(length=20):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def build_headers(token, alias):
    nonce = _gen_nonce()
    td = int(time.time())
    sign_str = f"{alias}_{nonce}_{td}_{SIGN_SALT}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    return {
        "X-Sc-Version": CLIENT_VERSION, "X-Sc-Nwt": "wifi", "X-Sc-Wf": "",
        "X-Sc-Nd": nonce, "X-Sc-Cloud": "0", "X-Sc-Platform": "windows",
        "X-Sc-Appid": APP_ID, "X-Sc-Alias": alias, "X-Sc-Od": token,
        "Content-Type": "application/x-www-form-urlencoded", "X-Sc-Ah": sign,
        "xweb_xhr": "1", "User-Agent": USER_AGENT, "X-Sc-Td": str(td), "Accept": "*/*",
    }


def _extract_list(data):
    if isinstance(data, dict):
        return data.get("list", []) or []
    if isinstance(data, list):
        return data
    return []


def img_urls(img_paths):
    if not img_paths:
        return []
    return [f"{CDN_BASE}/{p}{CDN_THUMB}" for p in img_paths if p]


class ZanaoClient:
    def __init__(self, token, alias):
        self.token = token
        self.alias = alias
        self.s = requests.Session()

    def _post(self, url):
        last_err = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = self.s.post(url, headers=build_headers(self.token, self.alias), timeout=20)
                break
            except requests.ConnectionError as e:
                last_err = NetworkError(f"网络不通: {e}")
            except requests.Timeout as e:
                last_err = NetworkError(f"请求超时: {e}")
            except requests.RequestException as e:
                last_err = NetworkError(f"请求失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
                continue
            raise last_err or NetworkError("未知网络错误")

        if r.status_code != 200:
            raise ZanaoError(f"HTTP {r.status_code}")
        try:
            j = r.json()
        except Exception:
            raise ZanaoError("响应不是 JSON（签名或接口可能已变更）")

        if j.get("errno") != 0:
            raise ZanaoError(f"errno={j.get('errno')} errmsg={j.get('errmsg', '')}")
        return j.get("data")

    # === 读接口 ===

    def hot(self):
        return _extract_list(self._post(f"{API_BASE}/thread/hot?count=10&type=3"))

    def list(self, from_time="0"):
        u = f"{API_BASE}/thread/v2/list?from_time={from_time}&with_comment=false&with_reply=false"
        return _extract_list(self._post(u))

    def search(self, keyword, page=1, history=False, range_time=None):
        cid = 20 if history else 10
        u = f"{API_BASE}/thread/v2/search?wd={quote(keyword)}&cur_page={page}&cate_id={cid}"
        if range_time:
            u += f"&range={range_time}"
        return _extract_list(self._post(u))

    def comments(self, thread_id):
        return _extract_list(self._post(f"{API_BASE}/comment/list?id={thread_id}"))

    def categories(self):
        data = self._post(f"{API_BASE}/catelist?from=post&is_cross=0&cross_all=1")
        if isinstance(data, dict):
            return data.get("cate_list", []) or []
        return []

    def user_info(self):
        return self._post(f"{API_BASE}/user/info?from=mine")

    def check_token(self):
        try:
            info = self.user_info()
            if isinstance(info, dict) and info.get("school_name"):
                return True, info
            return False, "token 有效但返回数据异常"
        except ZanaoError as e:
            return False, str(e)

    # === 写接口（点赞/取消赞，评论操作）===

    def like_post(self, thread_id):
        """点赞帖子。"""
        u = f"{API_BASE}/thread/like?id={thread_id}&comment_id=0&action=1"
        self._post(u)
        return True

    def unlike_post(self, thread_id):
        """取消点赞帖子。"""
        u = f"{API_BASE}/thread/like?id={thread_id}&comment_id=0&action=0"
        self._post(u)
        return True

    def like_comment(self, thread_id, comment_id):
        """点赞评论。"""
        u = f"{API_BASE}/comment/like?id={thread_id}&comment_id={comment_id}&action=1"
        self._post(u)
        return True

    def unlike_comment(self, thread_id, comment_id):
        """取消点赞评论。"""
        u = f"{API_BASE}/comment/like?id={thread_id}&comment_id={comment_id}&action=0"
        self._post(u)
        return True

    def post_comment(self, thread_id, content, reply_comment_id="0", root_comment_id="0", use_anon=0):
        u = (
            f"{API_BASE}/comment/post?id={thread_id}"
            f"&content={quote(content, safe='')}"
            f"&reply_comment_id={reply_comment_id}"
            f"&root_comment_id={root_comment_id}"
            f"&use_anon={use_anon}&from=detail"
        )
        self._post(u)
        return True

    def delete_comment(self, thread_id, comment_id):
        u = f"{API_BASE}/comment/delete?comment_id={comment_id}&id={thread_id}"
        self._post(u)
        return True

    def create_post(self, title, content, cate_id, img_paths="",
                    contact_person="", contact_phone="", contact_qq="", contact_wx="",
                    is_comment_close=0):
        u = (
            f"{API_BASE}/thread/post"
            f"?contact_person={quote(contact_person, safe='')}"
            f"&contact_phone={quote(contact_phone, safe='')}"
            f"&contact_qq={quote(contact_qq, safe='')}"
            f"&contact_wx={quote(contact_wx, safe='')}"
            f"&title={quote(title, safe='')}"
            f"&content={quote(content, safe='')}"
            f"&img_paths={quote(img_paths, safe='')}"
            f"&cate_id={cate_id}"
            f"&certShow=10"
            f"&is_comment_close={is_comment_close}"
        )
        self._post(u)
        return True

    def change_post_status(self, thread_id, action="finish"):
        u = f"{API_BASE}/thread/change?id={thread_id}&act={quote(action, safe='')}"
        self._post(u)
        return True

    def get_messages(self, from_time="0"):
        return _extract_list(self._post(f"{API_BASE}/msg/list?from_time={from_time}"))
