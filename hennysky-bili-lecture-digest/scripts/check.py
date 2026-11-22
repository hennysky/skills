#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交付前自检：页面是否自包含、逐字稿是否完整、有无排版残留。

用法: python3 check.py <项目目录>
退出码 0 = 通过（可能有 warn），1 = 有 fail。
"""
import json
import os
import re
import sys


def main():
    proj = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    checks, fails = [], 0

    def add(level, name, detail=""):
        nonlocal fails
        if level == "fail":
            fails += 1
        checks.append((level, name, detail))

    meta_p = os.path.join(proj, "meta.json")
    if not os.path.exists(meta_p):
        add("fail", "meta.json 存在", "先跑 fetch.py")
        meta = {}
    else:
        meta = json.load(open(meta_p, encoding="utf-8"))

    for f in ("transcript.md", "transcript.srt", "index.html"):
        p = os.path.join(proj, f)
        add("ok" if os.path.exists(p) else "fail", f"存在 {f}",
            f"{os.path.getsize(p) // 1024} KB" if os.path.exists(p) else "缺失")

    trans = open(os.path.join(proj, "transcript.md"), encoding="utf-8").read() if os.path.exists(
        os.path.join(proj, "transcript.md")) else ""
    segs = re.findall(r"^\*\*\[(\d{2}:\d{2})\]\*\*\s*(.+)$", trans, re.M)
    dur0 = meta.get("audio_seconds") or meta.get("duration") or 0
    add("ok" if len(segs) >= 8 else "fail", "逐字稿段数", f"{len(segs)} 段")

    def secs(ts):
        m, s = ts.split(":")
        return int(m) * 60 + int(s)

    times = [secs(t) for t, _ in segs]
    add("ok" if times == sorted(times) else "fail", "时间戳单调递增")
    dur = meta.get("audio_seconds") or meta.get("duration") or 0
    if dur and times:
        cover = times[-1] / dur * 100
        add("ok" if cover > 85 else "warn", "时间覆盖", f"最后一段在 {cover:.0f}% 处")

    chars = (meta.get("transcript") or {}).get("chars") or len(
        re.sub(r"^\*\*\[\d{2}:\d{2}\]\*\*", "", trans, flags=re.M))
    per_min = chars / (dur0 / 60) if dur0 else 0
    add("ok" if per_min > 120 else "warn", "语速密度",
        f"{chars:,} 字 / {per_min:.0f} 字每分钟（正常 200-350）")

    html_p = os.path.join(proj, "index.html")
    if os.path.exists(html_p):
        html = open(html_p, encoding="utf-8").read()
        ext = re.findall(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', html)
        add("ok" if not ext else "fail", "页面自包含", "无外部脚本/样式" if not ext else f"{len(ext)} 个外链")
        body = re.sub(r"<pre.*?</pre>", "", html, flags=re.S)
        body = re.sub(r"<[^>]+>", "", body)
        left = body.count("**")
        add("ok" if left == 0 else "warn", "无 markdown 残留", f"{left} 处 **")
        add("ok" if "id=\"segs\"" in html else "fail", "逐字稿区块", "")
        add("ok" if "seg[hidden]" in html else "warn", "搜索过滤样式", "缺 .seg[hidden] 会导致筛不掉")

    print(f"\n项目：{proj}")
    for lvl, name, detail in checks:
        mark = {"ok": "PASS", "warn": "WARN", "fail": "FAIL"}[lvl]
        print(f"  [{mark}] {name}{'  · ' + detail if detail else ''}")
    print(f"\n结果：{'通过' if fails == 0 else str(fails) + ' 项失败'}")
    sys.exit(0 if fails == 0 else 1)


if __name__ == "__main__":
    main()
