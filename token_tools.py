"""赞哦 token 自动刷新。

证书已信任、mitmproxy 已装好的前提下，一键刷新 token。
内置重试、进度显示、错误恢复。macOS / Windows 自适应。

用法: python3 ~/.agents/skills/zanao/zanao_refresh_token.py
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

# Windows 控制台默认 GBK 不支持 emoji，强制 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SKILL_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SKILL_DIR / "config.json"
TOKEN_FILE = str(Path(os.environ.get("TEMP", "/tmp")) / "zanao_token.txt")
GRABBER_SCRIPT = str(Path(os.environ.get("TEMP", "/tmp")) / "zanao_grabber.py")
LOG_FILE = str(Path(os.environ.get("TEMP", "/tmp")) / "mitmweb_refresh.log")

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

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
        with open(TF, "w", encoding="utf-8") as f:
            f.write(f"token={od}\\nalias={alias}\\n")
        print(f"\\n[抓到 token] alias={alias} token=...{od[-4:]}\\n")
"""


def _check_prereqs():
    """检查前置条件：mitmproxy 已装、证书已生成。"""
    if not shutil.which("mitmweb"):
        if IS_WIN:
            print("❌ mitmweb 未安装，运行: pip install mitmproxy")
        else:
            print("❌ mitmweb 未安装，运行: brew install mitmproxy")
        sys.exit(1)

    cert = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    if not cert.exists():
        print("⚠️  mitmproxy 证书未生成，将自动生成...")
        print(f"   证书路径: {cert}")
        print("   ⏳ 正在启动 mitmweb 生成证书...")
        # 临时启动 mitmweb 生成证书，生成后立即关闭
        log = open(LOG_FILE, "w", encoding="utf-8")
        tmp_proc = subprocess.Popen(
            ["mitmweb", "--no-web-open-browser", "--listen-port", "8080"],
            stdout=log, stderr=log,
        )
        time.sleep(4)
        for _ in range(15):
            if cert.exists():
                break
            time.sleep(1)
        tmp_proc.terminate()
        time.sleep(1)
        try:
            tmp_proc.kill()
        except Exception:
            pass
        log.close()
        if not cert.exists():
            print("❌ 证书仍未生成，请检查 mitmproxy 安装")
            sys.exit(1)

    # Windows: 确保证书已导入到受信任根
    if IS_WIN:
        cert_cer = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.cer"
        if cert_cer.exists():
            subprocess.run(
                ["certutil", "-addstore", "-user", "Root", str(cert_cer)],
                capture_output=True,
            )


def _kill_mitm():
    if IS_WIN:
        subprocess.run(["taskkill", "/F", "/IM", "mitmweb.exe"], capture_output=True)
    else:
        subprocess.run(["pkill", "-f", "mitmweb"], capture_output=True)


def _kill_wmpf():
    """Windows: 杀掉微信小程序框架进程，确保重启后读取新的代理设置。"""
    if not IS_WIN:
        return
    subprocess.run(["taskkill", "/F", "/IM", "WeChatAppEx.exe"], capture_output=True)
    time.sleep(1)


def _start_mitm():
    _kill_mitm()
    time.sleep(1)
    with open(GRABBER_SCRIPT, "w", encoding="utf-8") as f:
        f.write(GRABBER_CODE)
    env = os.environ.copy()
    env["ZANAO_TOKEN_FILE"] = TOKEN_FILE
    log = open(LOG_FILE, "w", encoding="utf-8")
    p = subprocess.Popen(
        ["mitmweb", "-s", GRABBER_SCRIPT, "--no-web-open-browser", "--listen-port", "8080"],
        stdout=log,
        stderr=log,
        env=env,
    )
    time.sleep(3)
    if p.poll() is not None:
        print("❌ mitmweb 启动失败！")
        with open(LOG_FILE) as f:
            print(f"   日志: {f.read()[:500]}")
        sys.exit(1)
    return p


def _proxy(enable):
    """设置/取消系统代理。macOS 用 networksetup，Windows 用注册表。"""
    if enable:
        if IS_MAC:
            subprocess.run(["networksetup", "-setwebproxy", "Wi-Fi", "127.0.0.1", "8080"])
            subprocess.run(["networksetup", "-setsecurewebproxy", "Wi-Fi", "127.0.0.1", "8080"])
        elif IS_WIN:
            # 微信 WMPF 只认用户级 Internet Settings 代理，不认 netsh winhttp
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "127.0.0.1:8080")
            winreg.CloseKey(key)
            # 杀掉 WMPF 使其重启后读取新代理
            _kill_wmpf()
        else:
            os.environ["http_proxy"] = "http://127.0.0.1:8080"
            os.environ["https_proxy"] = "http://127.0.0.1:8080"
    else:
        if IS_MAC:
            subprocess.run(["networksetup", "-setwebproxystate", "Wi-Fi", "off"])
            subprocess.run(["networksetup", "-setsecurewebproxystate", "Wi-Fi", "off"])
        elif IS_WIN:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        else:
            os.environ.pop("http_proxy", None)
            os.environ.pop("https_proxy", None)


def _wait(timeout=180):
    print(f"📡 等待赞哦请求（最多 {timeout} 秒，随时可 Ctrl+C 中断）...\n")
    t0 = time.time()
    dots = 0
    while time.time() - t0 < timeout:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, encoding="utf-8") as f:
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
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    old = cfg.get("zanao_token", "")
    cfg["zanao_token"] = token
    cfg["zanao_alias"] = alias
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
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
        _kill_mitm()
        sys.exit(0)

    signal.signal(signal.SIGINT, _on_sig)
    signal.signal(signal.SIGTERM, _on_sig)

    proc = None
    try:
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
        if IS_WIN:
            print("   ℹ️  已自动关闭微信小程序框架（下次打开小程序会重启）")

        # 用户操作 — 醒目的手动步骤提示
        print()
        print("┌" + "─" * 58 + "┐")
        print("│" + "  3/4  需要你手动操作（唯一需要你动手的步骤）          ".center(62) + "│")
        print("│" + " " * 58 + " │")
        print("│" + "   1. 打开电脑微信                                        ".center(62) + "│")
        print("│" + "   2. 进入赞噢小程序（如已打开请先完全关闭再重新进）       ".center(62) + "│")
        print("│" + "   3. 刷一下首页或热门，看到帖子列表即可                   ".center(62) + "│")
        print("│" + " " * 58 + " │")
        if IS_WIN:
            print("│" + "   注意：小程序框架已自动重启，确保能读到新代理设置       ".center(62) + "│")
            print("│" + " " * 58 + " │")
        print("├" + "─" * 58 + "┤")
        print("│" + "   完成后回到这里，按 Enter 开始自动抓取 token...         ".center(62) + "│")
        print("└" + "─" * 58 + "┘")
        input("   >>> ")

        # 等待
        try:
            token, alias = _wait(timeout=180)
        except Exception:
            token, alias = None, None

        # 正常清理
        print("\n4/4 清理...")
        _clean(proc)

        if token:
            changed = _update(token, alias)
            print(f"   {'✅ token 已更新' if changed else 'ℹ️  token 未变'}")
            print(f"      alias={alias}   末4位=...{token[-4:]}")
            print()
            print("=" * 40)
            print("🎉 完成！验证:")
            python_cmd = "python" if IS_WIN else "python3"
            print(f"   {python_cmd} ~/.agents/skills/zanao/zanao_client.py user")
            print("=" * 40)
        else:
            print("   ⚠️  未抓到赞哦请求")
            print()
            print("=" * 40)
            print("⏰ 超时 — 3 分钟内没抓到。可能原因：")
            print("   1. 没打开赞哦小程序或没登录")
            if IS_WIN:
                print("   2. 证书没信任（运行 certutil -addstore -user Root ~/.mitmproxy/mitmproxy-ca-cert.cer）")
                print("   3. 小程序没有重新打开（需要完全关闭再打开）")
            else:
                print('   2. 证书没信任（钥匙串里 mitmproxy 设"始终信任"）')
                print("   3. 代理没生效")
            print(f"   再试: {'python' if IS_WIN else 'python3'} ~/.agents/skills/zanao/zanao_refresh_token.py")
            print("=" * 40)
            sys.exit(1)
    finally:
        # 确保任何异常退出（EOFError、网络错误等）也能清理代理和进程
        _clean(proc)


if __name__ == "__main__":
    main()
