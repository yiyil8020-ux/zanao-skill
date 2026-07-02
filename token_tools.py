"""赞哦 token 自动刷新。

证书已在钥匙串、mitmproxy 已装好的前提下，一键刷新 token。
内置重试、进度显示、错误恢复。

用法: python3 scripts/zanao_refresh_token.py
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SKILL_DIR / "config.json"
TOKEN_FILE = "/tmp/zanao_token.txt"
GRABBER_SCRIPT = "/tmp/zanao_grabber.py"
LOG_FILE = "/tmp/mitmweb_refresh.log"

GRABBER_CODE = """
from mitmproxy import http
import os

TF = os.environ.get("ZANAO_TOKEN_FILE", "/tmp/zanao_token.txt")

def request(flow: http.HTTPFlow):
    if "api.x.zanao.com" not in flow.request.pretty_host:
        return
    od = flow.request.headers.get("X-Sc-Od", "")
    alias = flow.request.headers.get("X-Sc-Alias", "")
    if od:
        with open(TF, "w") as f:
            f.write(f"token={od}\\nalias={alias}\\n")
        print(f"\\n[抓到 token] alias={alias} token=...{od[-4:]}\\n")
"""


def _check_prereqs():
    """检查前置条件：mitmproxy 已装、证书已生成。"""
    if not shutil.which("mitmweb"):
        print("❌ mitmweb 未安装，运行: brew install mitmproxy")
        sys.exit(1)
    cert = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    if not cert.exists():
        print("⚠️  mitmproxy 证书未生成，将尝试自动生成...")
        print("   首次运行 mitmweb 会自动生成，但你需要手动在钥匙串里设「始终信任」")
        print("   证书生成路径: ~/.mitmproxy/mitmproxy-ca-cert.pem")


def _start_mitm():
    subprocess.run(["pkill", "-f", "mitmweb"], capture_output=True)
    time.sleep(1)
    with open(GRABBER_SCRIPT, "w") as f:
        f.write(GRABBER_CODE)
    env = os.environ.copy()
    env["ZANAO_TOKEN_FILE"] = TOKEN_FILE
    log = open(LOG_FILE, "w")
    p = subprocess.Popen(
        ["mitmweb", "-s", GRABBER_SCRIPT, "--no-web-open-browser", "--listen-port", "8080"],
        stdout=log, stderr=log, env=env,
    )
    time.sleep(3)
    if p.poll() is not None:
        print("❌ mitmweb 启动失败！")
        with open(LOG_FILE) as f:
            print(f"   日志: {f.read()[:500]}")
        sys.exit(1)
    return p


def _proxy(enable):
    if enable:
        if sys.platform == "darwin":
            subprocess.run(["networksetup", "-setwebproxy", "Wi-Fi", "127.0.0.1", "8080"])
            subprocess.run(["networksetup", "-setsecurewebproxy", "Wi-Fi", "127.0.0.1", "8080"])
        elif sys.platform == "win32":
            subprocess.run(["netsh", "winhttp", "set", "proxy", "127.0.0.1:8080"], shell=True)
        else:
            os.environ["http_proxy"] = "http://127.0.0.1:8080"
            os.environ["https_proxy"] = "http://127.0.0.1:8080"
    else:
        if sys.platform == "darwin":
            subprocess.run(["networksetup", "-setwebproxystate", "Wi-Fi", "off"])
            subprocess.run(["networksetup", "-setsecurewebproxystate", "Wi-Fi", "off"])
        elif sys.platform == "win32":
            subprocess.run(["netsh", "winhttp", "reset", "proxy"], shell=True)
        else:
            os.environ.pop("http_proxy", None)
            os.environ.pop("https_proxy", None)


def _wait(timeout=180):
    print(f"📡 等待赞哦请求（最多 {timeout} 秒，随时可 Ctrl+C 中断）...\n")
    t0 = time.time()
    dots = 0
    while time.time() - t0 < timeout:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE) as f:
                content = f.read().strip()
            token, alias = None, "lzu"
            for line in content.split("\n"):
                if line.startswith("token="):
                    token = line.split("=", 1)[1]
                elif line.startswith("alias="):
                    alias = line.split("=", 1)[1]
            if token:
                return token, alias
        dots = (dots + 1) % 10
        sys.stdout.write(f"\r   {'·' * dots}{' ' * (10 - dots)}")
        sys.stdout.flush()
        time.sleep(2)
    sys.stdout.write("\r" + " " * 20 + "\r")
    return None, None


def _update(token, alias):
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    old = cfg.get("zanao_token", "")
    cfg["zanao_token"] = token
    cfg["zanao_alias"] = alias
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    changed = old != token
    return changed


def _clean(proc):
    _proxy(False)
    if proc:
        proc.terminate()
        time.sleep(1)
        try:
            proc.kill()
        except Exception:
            pass
    for f in [TOKEN_FILE, GRABBER_SCRIPT, LOG_FILE]:
        try:
            os.remove(f)
        except Exception:
            pass


def main():
    # Ctrl+C 时也做清理
    def _on_sig(signum, frame):
        print("\n\n⚠️  中断！正在清理...")
        _proxy(False)
        subprocess.run(["pkill", "-f", "mitmweb"], capture_output=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, _on_sig)
    signal.signal(signal.SIGTERM, _on_sig)

    print("=" * 40)
    print("🔑 赞哦 token 自动刷新")
    print("=" * 40)

    # 前置检查
    _check_prereqs()

    # 启动
    print("\n1/4 启动 mitmproxy...")
    proc = _start_mitm()
    print(f"   ✅ PID {proc.pid}   网页: http://127.0.0.1:8081")

    # 代理
    print("2/4 设系统代理...")
    _proxy(True)
    print("   ✅ 127.0.0.1:8080")

    # 用户操作
    print()
    print("3/4 👆 唯一手动步骤：电脑端微信 → 赞哦小程序 → 刷一下首页/热门")
    print()

    # 等待
    try:
        token, alias = _wait(timeout=180)
    except Exception:
        token, alias = None, None

    # 清理
    print("\n4/4 清理...")
    _clean(proc)

    if token:
        changed = _update(token, alias)
        print(f"   {'✅ token 已更新' if changed else 'ℹ️  token 未变'}")
        print(f"      alias={alias}   末4位=...{token[-4:]}")
        print()
        print("=" * 40)
        print("🎉 完成！验证:")
        print("   .venv/bin/python3 scripts/zanao_client.py user")
        print("=" * 40)
    else:
        print("   ⚠️  未抓到赞哦请求")
        print()
        print("=" * 40)
        print("⏰ 超时 — 3 分钟内没抓到。可能原因：")
        print("   1. 没打开赞哦小程序或没登录")
        print('   2. 证书没信任（钥匙串里 mitmproxy 设"始终信任"）')
        print("   3. 代理没生效")
        print("   再试: python3 scripts/zanao_refresh_token.py")
        print("=" * 40)
        sys.exit(1)


if __name__ == "__main__":
    main()
