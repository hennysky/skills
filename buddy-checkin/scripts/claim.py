#!/usr/bin/env python3
"""Buddy加油站积分自动领取（领取账号当前所有可自动领取的积分）

用法:
  python3 claim.py login      # 一次性登录（弹浏览器，微信扫码），保存会话
  python3 claim.py claim      # 每日执行（无界面）：每日签到 + Buddy出车奖励 + 查余额
  python3 claim.py status     # 只查签到状态，不领取

调度说明:
  系统级定时器（launchd/cron）在本机被 macOS 安全策略禁止第三方进程注册，
  因此定时调度由 WorkBuddy 自动化任务「每日自动领Buddy加油站积分」承担
  （每日 09:30，调用本脚本 claim）。技能安装时确认该自动化存在即可。

设计说明:
  不模拟点击界面（需 macOS 辅助功能授权），而是复用网页版登录态在页面上下文
  里 fetch 平台自身接口（自动带 Keycloak 会话 cookie，SSO 静默续期）。
  已知可自动领取的积分类型:
    1. 每日签到        POST /billing/meter/daily-checkin
    2. Buddy出车奖励   POST /activity/growth/buddy/travel/claim （幂等；无奖励时 403 no unclaimed travel）
  无法自动领取的类型（需真人操作，脚本会跳过）: 邀请好友奖励、购买返利等。
"""
import json
import os
import subprocess
import sys
import time

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
STATE_FILE = os.path.join(DATA_DIR, "session.json")
TOKEN_FILE = os.path.join(DATA_DIR, "token.json")
VENV_DIR = os.path.join(SKILL_DIR, ".venv")
APP_URL = "https://www.workbuddy.cn/app"
API = "https://www.workbuddy.cn"


# ---------------- 运行环境自愈（换机器/换人都能自己跑起来） ----------------

def _ensure_playwright():
    """确保当前解释器能 import playwright；缺了就建技能自带的 venv 并装好。"""
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        pass

    venv_py = os.path.join(VENV_DIR, "bin", "python3")
    if not os.path.exists(venv_py):
        print("SETUP 首次运行：正在准备浏览器环境（约 1 分钟）…", flush=True)
        base = sys.executable or "python3"
        try:
            subprocess.run([base, "-m", "venv", VENV_DIR], check=True, capture_output=True)
        except Exception as e:  # noqa: BLE001
            print("ENV_FAIL 无法创建虚拟环境：%s" % e, flush=True)
            return False
        pip = os.path.join(VENV_DIR, "bin", "pip")
        r = subprocess.run([pip, "install", "-q", "playwright"], capture_output=True, text=True)
        if r.returncode != 0:
            print("ENV_FAIL playwright 安装失败：%s" % (r.stderr or r.stdout)[-300:], flush=True)
            return False
        print("SETUP 浏览器环境就绪", flush=True)

    # 用自带 venv 的解释器重新执行本脚本
    os.execv(venv_py, [venv_py, os.path.abspath(__file__)] + sys.argv[1:])
    return False  # 不会执行到


def _launch(pw, headless):
    """优先用系统 Chrome（无需下载）；没有就退回 Playwright 自带 chromium 并自动安装。"""
    last = None
    for kwargs in ({"channel": "chrome"}, {}):
        try:
            return pw.chromium.launch(headless=headless, **kwargs)
        except Exception as e:  # noqa: BLE001
            last = e
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, timeout=600)
        return pw.chromium.launch(headless=headless)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("浏览器启动失败：%s | %s" % (last, e))



def _save(obj, path, mode=0o600):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)
    os.chmod(path, mode)


def _load(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _harvest_token(context, page):
    """登录后从 localStorage / cookie 里找出可用的 Bearer 令牌（含 JWT 模式）。"""
    import re

    jwt = re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}")
    found = {}
    try:
        ls = page.evaluate(
            """() => { const o={}; for (let i=0;i<localStorage.length;i++){const k=localStorage.key(i);o[k]=localStorage.getItem(k);} return o; }"""
        )
    except Exception:
        ls = {}
    for k, v in (ls or {}).items():
        if not isinstance(v, str):
            continue
        m = jwt.search(v)
        if m:
            _save({"key": k, "value": m.group(0), "kind": "jwt", "saved_at": time.time()}, TOKEN_FILE)
            found["jwt@" + k] = m.group(0)[:30] + "***(len=%d)" % len(m.group(0))
    for c in context.cookies():
        if jwt.search(c.get("value") or ""):
            m = jwt.search(c["value"])
            _save({"key": c["name"], "value": m.group(0), "kind": "jwt-cookie", "saved_at": time.time()}, TOKEN_FILE)
            found["jwt-cookie@" + c["name"]] = m.group(0)[:30] + "***"
    if not found:
        interesting = {
            k: (v[:60] + "…(len=%d)" % len(v))
            for k, v in ls.items()
            if isinstance(v, str) and any(t in k.lower() for t in ("token", "auth", "user", "session", "login")) and v
        }
        found["candidates"] = interesting
    return found


def cmd_login():
    if not _ensure_playwright():
        return 5
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = _launch(p, headless=False)
        context = browser.new_context(viewport={"width": 1100, "height": 850})
        page = context.new_page()
        page.goto(APP_URL, wait_until="domcontentloaded", timeout=60000)
        print("已打开登录页，请用微信扫码（只需这一次）…", flush=True)

        try:
            page.bring_to_front()
        except Exception:
            pass

        deadline = time.time() + 300
        logged = False
        stable = 0
        while time.time() < deadline:
            try:
                url = page.url
                on_app = url.startswith("https://www.workbuddy.cn/app") and "/login" not in url
                # 必须连续 3 次稳定停在 /app，避免登录页跳转瞬间被误判
                if on_app:
                    stable += 1
                else:
                    stable = 0
                if stable >= 3:
                    if page.evaluate(
                        "() => { const s=JSON.stringify(localStorage); return s.length>3000 || document.cookie.length>0; }"
                    ):
                        logged = True
                        break
            except Exception:
                pass
            page.wait_for_timeout(2000)

        if not logged:
            print("LOGIN_TIMEOUT 未检测到登录完成", flush=True)
            browser.close()
            return 2

        page.wait_for_timeout(5000)
        cookies = context.cookies()
        _save({"cookies": cookies, "saved_at": time.time()}, STATE_FILE)
        got = _harvest_token(context, page)
        print("LOGIN_OK url=%s cookies=%d" % (page.url, len(cookies)), flush=True)
        print("TOKEN_KEYS %s" % json.dumps(got, ensure_ascii=False)[:600], flush=True)
        browser.close()
        return 0


def _request_headers():
    tok = _load(TOKEN_FILE)
    headers = {"Content-Type": "application/json", "Origin": API, "Referer": APP_URL + "/"}
    if tok and tok.get("value"):
        headers["Authorization"] = "Bearer " + tok["value"]
    return headers


def _page_json(page, path):
    """在页面上下文里发 fetch（自动带 cookie，SSO 静默刷新后也能用）。"""
    return page.evaluate(
        """async (path) => {
            const r = await fetch(path, {
                method: 'POST',
                credentials: 'include',
                headers: {'Content-Type': 'application/json'},
                body: '{}'
            });
            let body = await r.text();
            return {status: r.status, body: body.slice(0, 1200)};
        }""",
        path,
    )


def _open_app():
    """打开无头浏览器进入 /app；返回 (page, context, browser) 或 (None, None, None)。"""
    if not _ensure_playwright():
        return None, None, None
    from playwright.sync_api import sync_playwright

    state = _load(STATE_FILE)
    if not state:
        print("NEED_LOGIN 尚未登录，请先执行 login", flush=True)
        return None, None, None
    pw = sync_playwright().start()
    browser = _launch(pw, headless=True)
    context = browser.new_context(storage_state=state)
    page = context.new_page()
    page.goto(APP_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)
    if "/login" in page.url:
        print("NEED_LOGIN 会话已失效，需要重新执行 login", flush=True)
        browser.close()
        pw.stop()
        return None, None, None
    return page, context, browser


def cmd_status():
    page, context, browser = _open_app()
    if not page:
        return 3
    res = _page_json(page, "/billing/meter/checkin-status")
    print("STATUS", json.dumps(res, ensure_ascii=False), flush=True)
    _save(context.storage_state(), STATE_FILE)
    browser.close()
    return 0


def cmd_claim():
    page, context, browser = _open_app()
    if not page:
        return 3

    overall = "OK"

    # ---- 1) 每日签到（状态接口不可信，一律以领取接口返回码为准）----
    res = _page_json(page, "/billing/meter/daily-checkin")
    print("CLAIM", json.dumps(res, ensure_ascii=False), flush=True)
    try:
        p2 = json.loads(res.get("body") or "{}")
    except Exception:
        p2 = {}
    code = p2.get("code")
    msg = str(p2.get("msg") or "")
    if code == 0:
        checkin = "OK"
        data = p2.get("data") if isinstance(p2.get("data"), dict) else {}
        credit = data.get("credit") or data.get("credits")
        if credit:
            print("CREDIT", credit, flush=True)
    elif code == 10001 or "已签到" in msg or "已领取" in msg or "明天再来" in msg:
        checkin = "ALREADY_CLAIMED"
        print("ALREADY_CLAIMED 今日已签到（'%s'）" % msg, flush=True)
    else:
        checkin = "FAIL"
        overall = "FAIL"
        print("CHECKIN_FAIL msg=%s" % msg, flush=True)
    print("CHECKIN_RESULT", checkin, flush=True)

    # ---- 2) Buddy 出车奖励（幂等；无奖励时 403 no unclaimed travel）----
    res3 = _page_json(page, "/activity/growth/buddy/travel/claim")
    print("TRAVEL", json.dumps(res3, ensure_ascii=False), flush=True)
    try:
        p3 = json.loads(res3.get("body") or "{}")
    except Exception:
        p3 = {}
    tcode = p3.get("code")
    tmsg = str(p3.get("msg") or "")
    if res3.get("status") == 200 and tcode == 0:
        travel = "OK"
        tdata = p3.get("data") if isinstance(p3.get("data"), dict) else {}
        print("TRAVEL_CREDIT %s" % (tdata.get("credit") or tdata.get("reward_credit") or "?"), flush=True)
    elif "no unclaimed travel" in tmsg or "未出车" in tmsg or res3.get("status") == 403:
        travel = "NONE"
        print("TRAVEL_NONE 暂无可领的出车奖励", flush=True)
    else:
        travel = "FAIL"
        print("TRAVEL_FAIL msg=%s" % tmsg, flush=True)
    print("TRAVEL_RESULT", travel, flush=True)

    # ---- 3) 查积分余额 ----
    try:
        res4 = _page_json(page, "/billing/meter/get-user-resource-summary")
        p4 = json.loads(res4.get("body") or "{}")
        total = (p4.get("data") or {}).get("TotalCredits")
        if total:
            print("BALANCE %s" % total, flush=True)
    except Exception:
        pass

    _save(context.storage_state(), STATE_FILE)
    browser.close()

    # 出车 FAIL 不影响整体（偶发），签到失败才算失败
    print("OVERALL", overall, flush=True)
    return 0 if overall == "OK" else 4


def cmd_doctor():
    """自检：环境 / 登录态 / 接口连通性。装好后先跑这个。"""
    ok = True
    print("SKILL_DIR", SKILL_DIR, flush=True)

    have = True
    try:
        import playwright  # noqa: F401
    except Exception:
        have = False
    print("PLAYWRIGHT", "ok" if have else "missing（首次运行 claim 会自动安装）", flush=True)

    chrome = os.path.exists("/Applications/Google Chrome.app")
    print("CHROME", "ok" if chrome else "missing（将使用 Playwright 自带 chromium）", flush=True)

    if not _load(STATE_FILE):
        print("SESSION missing（需要先执行 login 扫码一次）", flush=True)
        ok = False
    else:
        print("SESSION ok", flush=True)

    if ok:
        page, context, browser = _open_app()
        if not page:
            return 3
        res = _page_json(page, "/billing/meter/checkin-status")
        print("CHECKIN_STATUS http=%s" % res.get("status"), flush=True)
        _save(context.storage_state(), STATE_FILE)
        browser.close()
        print("DOCTOR_OK 一切正常", flush=True)
        return 0
    print("DOCTOR_TODO 按上面提示补齐后重跑", flush=True)
    return 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "claim"
    fn = {"login": cmd_login, "claim": cmd_claim, "status": cmd_status, "doctor": cmd_doctor}.get(cmd)
    if fn is None:
        print("unknown command:", cmd)
        sys.exit(1)
    sys.exit(fn())
