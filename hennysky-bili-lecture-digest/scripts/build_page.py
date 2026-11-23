#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成单文件 HTML 讲义：meta.json + analysis.md + transcript.md → index.html

用法:
  python3 build_page.py <项目目录> [--title 覆盖标题] [--out 文件名]

产物：自包含单文件，无外部资源，可离线打开、可打印。
"""
import argparse
import html as H
import json
import os
import re
import sys

MATHMAP = [("\\cdots", "⋯"), ("\\alpha", "α"), ("\\beta", "β"), ("\\sigma", "σ"),
           ("\\mu", "μ"), ("\\times", "×"), ("\\cdot", "·"), ("\\approx", "≈"),
           ("\\leq", "≤"), ("\\geq", "≥"), ("\\sum", "∑"), ("\\lvert", "|"),
           ("\\rvert", "|"), ("\\%", "%"), ("\\,", " "), ("\\left", ""), ("\\right", "")]


def esc(s):
    return H.escape(str(s), quote=False)


def mathhtml(src):
    s = esc(src.strip())
    for a, b in MATHMAP:
        s = s.replace(a, b)
    s = re.sub(r"\s*=\s*", ' <span class="eq">=</span> ', s)
    s = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"_([0-9A-Za-z])", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{([^{}]*)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"\^([0-9A-Za-z])", r"<sup>\1</sup>", s)
    for _ in range(5):
        s2 = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}",
                    r'<span class="frac"><span class="n">\1</span><span class="d">\2</span></span>', s)
        if s2 == s:
            break
        s = s2
    s = re.sub(r"\\sqrt\{([^{}]*)\}", r'<span class="rad">&radic;<span class="rb">\1</span></span>', s)
    return re.sub(r" {2,}", " ", s)


def inline(s):
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    s = re.sub(r"`([^`]+)`", keep_code, s)
    maths = []

    def keep_math(m):
        maths.append(mathhtml(m.group(1)))
        return f"\x01{len(maths) - 1}\x01"

    s = re.sub(r"\$\$(.+?)\$\$", keep_math, s)
    s = re.sub(r"\$([^$]+?)\$", keep_math, s)
    s = esc(s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: "<code>" + esc(codes[int(m.group(1))]) + "</code>", s)
    return re.sub(r"\x01(\d+)\x01", lambda m: maths[int(m.group(1))], s)


def md_to_html(text, toc):
    """toc: 收集 (level, text, id)"""
    lines = text.split("\n")
    out, i, n = [], 0, len(text.split("\n"))
    hcount = 0
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("<figure"):
            depth = s.count("<figure") - s.count("</figure>")
            buf = [s]
            i += 1
            while i < n and depth > 0:
                line = lines[i]
                buf.append(line)
                depth += line.count("<figure") - line.count("</figure>")
                i += 1
            out.append("\n".join(buf))
            continue

        if s.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + esc("\n".join(buf)) + "</code></pre>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            lvl, txt = len(m.group(1)), m.group(2).strip()
            if lvl == 1:
                out.append(f"<h2 class=\"sec-t\">{inline(txt)}</h2>")
            elif lvl == 2:
                hcount += 1
                hid = f"s{hcount}"
                toc.append((txt, hid))
                out.append(f'<h2 id="{hid}">{inline(txt)}</h2>')
            else:
                out.append(f"<h{lvl}>{inline(txt)}</h{lvl}>")
            i += 1
            continue
        if s.startswith("> "):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append('<div class="note">' + "<br>".join(inline(x) for x in buf if x) + "</div>")
            continue
        if re.match(r"^---+$", s):
            out.append("<hr>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1].strip()):
            head = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            t = ['<div class="tw"><table><thead><tr>']
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                r = (r + [""] * len(head))[:len(head)]
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        m = re.match(r"^(\d+)\.\s+(.*)$", s)
        if m:
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        if re.match(r"^[-*]\s+", s):
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            out.append('<div class="formula">' + mathhtml(s[2:-2]) + "</div>")
            i += 1
            continue
        buf = [s]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith(("#", ">", "|", "-", "*", "```"))
                    or re.match(r"^\d+\.\s", nxt) or re.match(r"^---+$", nxt)):
                break
            buf.append(nxt)
            i += 1
        out.append(f"<p>{inline(''.join(buf))}</p>")
    return "\n".join(out)


def human_duration(sec):
    sec = int(sec or 0)
    return f"{sec // 3600}h{sec % 3600 // 60:02d}m" if sec >= 3600 else f"{sec // 60}m{sec % 60:02d}s"


CSS = r"""
:root{
  --bg:#080d12; --elev:#0d141b; --card:#101820; --ink:#eef3f8; --muted:#93a1ae;
  --line:#1e2b37; --accent:#43d0b0; --accent2:#f0a35f; --soft:rgba(67,208,176,.08);
  --grid:rgba(255,255,255,.026); --code:#0b1218; --mark:#6b5a1e; --base:19.5px;
}
html[data-theme=light]{
  --bg:#f4f6f8; --elev:#fff; --card:#fff; --ink:#0d1319; --muted:#55606c;
  --line:#dbe1e7; --accent:#0e6b58; --accent2:#b4451f; --soft:rgba(14,107,88,.07);
  --grid:rgba(13,19,25,.035); --code:#eef1f4; --mark:#ffe9a8;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;font-size:var(--base)}
body{margin:0;background:var(--bg);color:var(--ink);
  font:1rem/1.9 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",sans-serif;
  -webkit-font-smoothing:antialiased;letter-spacing:.005em}
body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:34px 34px;
  mask-image:radial-gradient(1200px 800px at 50% 0%,#000 40%,transparent 100%)}
body>*{position:relative;z-index:1}
a{color:var(--accent);text-underline-offset:3px}
code{font:.86em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);padding:.14em .4em;border-radius:3px;overflow-wrap:anywhere}
#bar{position:fixed;top:0;left:0;height:2px;width:0;background:var(--accent);z-index:99}

.hero{padding:84px 0 46px;border-bottom:1px solid var(--line);position:relative}
.hero::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
  background:linear-gradient(90deg,var(--accent),transparent 60%);opacity:.55}
.wrap{max-width:1320px;margin:0 auto;padding:0 44px}
.kicker{display:flex;gap:16px;align-items:center;font:11.5px ui-monospace,Menlo,monospace;
  letter-spacing:.24em;color:var(--accent);text-transform:uppercase;margin-bottom:30px}
.kicker::after{content:"";flex:1;height:1px;background:var(--line)}
h1{font-size:clamp(44px,4.6vw,74px);line-height:1.04;letter-spacing:-.03em;margin:0 0 22px;font-weight:800;
  background:linear-gradient(180deg,var(--ink),color-mix(in srgb,var(--ink) 92%,transparent));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.sub{font-size:1.18rem;line-height:1.7;color:var(--muted);max-width:46em;margin:0 0 34px}
.meta{display:flex;gap:34px;flex-wrap:wrap;font-size:.78rem;color:var(--muted);margin:0;padding:0;list-style:none}
.meta b{color:var(--ink);font-weight:600;font-family:ui-monospace,Menlo,monospace}
.stats{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);border-radius:3px;overflow:hidden;margin:40px 0 0}
.st{background:var(--elev);padding:22px 26px;border-right:1px solid var(--line)}
.st:last-child{border-right:0}
.st .v{font:600 2rem/1.2 ui-monospace,Menlo,monospace;letter-spacing:-.03em;color:var(--accent)}
.st .k{font-size:.72rem;color:var(--muted);margin-top:7px;letter-spacing:.1em}

.shell{display:grid;grid-template-columns:206px minmax(0,1fr);gap:72px;max-width:1320px;margin:0 auto;padding:64px 44px 120px}
nav.toc{position:sticky;top:30px;align-self:start;font-size:.86rem}
nav.toc h6{font:11px ui-monospace,Menlo,monospace;letter-spacing:.24em;color:var(--muted);margin:0 0 18px}
nav.toc a{display:block;color:var(--muted);text-decoration:none;padding:7px 0 7px 14px;
  border-left:1px solid var(--line);line-height:1.5;transition:color .15s;font-size:.8rem}
nav.toc a:hover{color:var(--ink)}
nav.toc a.on{color:var(--accent);border-left-color:var(--accent);font-weight:600}
.themebtn{margin-top:8px;font:11.5px ui-monospace,Menlo,monospace;letter-spacing:.1em;color:var(--muted);
  background:transparent;border:1px solid var(--line);border-radius:2px;padding:7px 12px;cursor:pointer;display:block;width:100%;text-align:left}
.themebtn:hover{color:var(--accent);border-color:var(--accent)}

section{margin-bottom:104px;scroll-margin-top:26px;min-width:0}
.sec-head{display:flex;gap:18px;align-items:flex-start;border-bottom:1px solid var(--line);
  padding-bottom:14px;margin-bottom:40px}
.sec-no{font:600 12.5px ui-monospace,Menlo,monospace;color:var(--accent);letter-spacing:.12em;
  padding:8px 0 0 12px;border-left:2px solid var(--accent)}
.sec-t{font-size:clamp(32px,3.2vw,42px);font-weight:800;letter-spacing:-.025em;margin:0;line-height:1.15}

h2{font-size:1.52rem;line-height:1.45;letter-spacing:-.015em;margin:60px 0 18px;font-weight:750;max-width:30em}
h3{font-size:1.24rem;line-height:1.55;margin:46px 0 14px;font-weight:700;max-width:32em}
h4{font-size:1.04rem;margin:32px 0 10px;font-weight:700;color:var(--muted);letter-spacing:.02em}
p{margin:0 0 1.05rem;max-width:42em}
ul,ol{margin:0 0 1.1rem;padding-left:1.5em;max-width:42em}
li{margin:7px 0}
hr{border:0;border-top:1px solid var(--line);margin:46px 0}
.note{border-left:2px solid var(--accent);background:var(--soft);padding:17px 22px;border-radius:0;
  color:var(--muted);font-size:.96rem;line-height:1.8;margin:0 0 26px;max-width:42em}
.note strong{color:var(--ink)}
pre{background:var(--code);border:1px solid var(--line);border-radius:3px;padding:18px 20px;overflow:auto;
  font-size:.82rem;line-height:1.8;min-width:0;max-width:100%}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:3px;margin:0 0 28px;min-width:0;max-width:100%}
table{border-collapse:collapse;width:100%;font-size:.92rem;line-height:1.75;min-width:720px}
th,td{padding:15px 18px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;min-width:5.5em}
th{background:var(--elev);font:600 11.5px ui-monospace,Menlo,monospace;color:var(--muted);
  letter-spacing:.1em;text-transform:uppercase;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:var(--soft)}
.formula{display:flex;justify-content:center;align-items:center;margin:12px 0 28px;padding:20px;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line);
  font-family:"Times New Roman",serif;font-size:1.75rem;overflow-x:auto;color:var(--ink)}
.frac{display:inline-flex;flex-direction:column;text-align:center;vertical-align:middle;margin:0 5px;line-height:1.2}
.frac .n{border-bottom:1.2px solid currentColor;padding:0 5px 2px}
.frac .d{padding:2px 5px 0}
.rad .rb{border-top:1.1px solid currentColor;padding:0 3px;margin-left:1px}
sub,sup{font-size:.7em;line-height:0}
.fig{margin:34px 0 40px;background:var(--card);border:1px solid var(--line);padding:30px 30px 18px;position:relative;max-width:100%}
.fig::before{content:"";position:absolute;inset:7px;border:1px dashed var(--line);opacity:.5;pointer-events:none}
.fig figcaption{font-size:.8rem;color:var(--muted);line-height:1.85;margin-top:18px;
  border-top:1px solid var(--line);padding-top:13px;position:relative;max-width:60em}
.fig svg{width:100%;height:auto;display:block;position:relative}
.fno{display:inline-block;font:11px ui-monospace,Menlo,monospace;letter-spacing:.14em;
  color:var(--accent);margin-right:10px;text-transform:uppercase}
.flow{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.node{display:inline-block;background:var(--elev);border:1px solid var(--line);border-radius:3px;
  padding:11px 19px;font-size:.95rem}
.node.accent{background:var(--accent);border-color:var(--accent);color:#062b24;font-weight:700}
html[data-theme=light] .node.accent{color:#fff}
.node.ghost{background:transparent;color:var(--muted)}
.arrow{color:#6d7a87;font-size:1rem}
.steps4{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.steps4 .st{background:var(--elev);border:1px solid var(--line);border-radius:3px;padding:20px;
  position:relative;display:flex;flex-direction:column;gap:6px}
.steps4 .num{font:600 11.5px ui-monospace,Menlo,monospace;color:#062b24;background:var(--accent);
  width:23px;height:23px;border-radius:2px;display:flex;align-items:center;justify-content:center;margin-bottom:10px}
.steps4 b{font-size:.98rem}
.steps4 small{color:var(--muted);font-size:.8rem;line-height:1.7}
.tree{list-style:none;margin:0;padding:0;font-size:.95rem;line-height:1.85}
.tree ul{list-style:none;margin:6px 0 6px 12px;padding-left:24px;border-left:1px solid var(--line)}
.tree>li{padding:6px 0}.tree li{position:relative}
.tree ul>li::before{content:"";position:absolute;left:-24px;top:22px;width:16px;height:1px;background:var(--line)}
.tree .q{font-weight:650}.tree .yes{color:var(--accent)}.tree .no{color:var(--accent2)}
.tree .note-i{color:var(--muted);font-size:.82rem}
.pipe{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.pnode{background:var(--elev);border:1px solid var(--line);border-radius:3px;padding:10px 17px;font-size:.94rem}
.pnode.accent{background:var(--accent);color:#062b24;border-color:var(--accent);font-weight:700}
.parrow{color:#6d7a87}


.tbar{position:sticky;top:0;z-index:6;background:var(--bg);padding:16px 0;display:flex;gap:14px;
  align-items:center;border-bottom:1px solid var(--line);margin-bottom:4px}
.tbar input{flex:1;min-width:0;font:1rem inherit;color:var(--ink);background:var(--elev);
  border:1px solid var(--line);border-radius:3px;padding:12px 16px;outline:none}
.tbar input:focus{border-color:var(--accent)}
.tbar .count{font:12px ui-monospace,Menlo,monospace;color:var(--muted);white-space:nowrap;letter-spacing:.06em}
.seg{display:grid;grid-template-columns:70px minmax(0,1fr);gap:22px;padding:15px 0;border-bottom:1px solid var(--line)}
.seg[hidden]{display:none}
.seg:hover{background:var(--soft)}
.seg .ts{font:12.5px/2 ui-monospace,Menlo,monospace;color:var(--accent2);padding-top:5px;cursor:copy;letter-spacing:.04em}
.seg p{margin:0;font-size:1.04rem;line-height:2;max-width:52em}
.seg mark{background:var(--mark);color:inherit}

footer{border-top:1px solid var(--line);padding:38px 0 80px;color:var(--muted);font-size:.82rem}
#top{position:fixed;right:28px;bottom:28px;width:44px;height:44px;border-radius:2px;border:1px solid var(--line);
  background:var(--elev);color:var(--muted);cursor:pointer;display:none;font-size:16px}
#top.show{display:block}
@media print{
  nav.toc,.tbar,#top,#bar,body::before{display:none!important}
  .shell{grid-template-columns:1fr;padding:0}
  .fig,table,.formula{page-break-inside:avoid}
  body{background:#fff;color:#000}
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--title")
    ap.add_argument("--out", default="index.html")
    args = ap.parse_args()

    proj = os.path.abspath(args.project)
    meta = json.load(open(os.path.join(proj, "meta.json"), encoding="utf-8"))
    analysis_path = os.path.join(proj, "analysis.md")
    analysis = open(analysis_path, encoding="utf-8").read() if os.path.exists(analysis_path) else ""
    trans_path = os.path.join(proj, "transcript.md")
    trans = open(trans_path, encoding="utf-8").read() if os.path.exists(trans_path) else ""

    raw_title = args.title or meta.get("title") or "视频讲义"
    title = raw_title
    if not args.title and "---" in title:
        title = title.split("---")[0].strip()
    tr = meta.get("transcript") or {}
    segs = re.findall(r"^\*\*\[(\d{2}:\d{2})\]\*\*\s*(.+)$", trans, re.M)
    chars = tr.get("chars") or sum(len(t) for _, t in segs)

    toc = []
    body = md_to_html(analysis, toc) if analysis else (
        '<div class="note">还没有写拆解。运行流程后由模型生成 <code>analysis.md</code>，再重新构建。</div>')

    seg_html = "".join(
        f'<div class="seg" data-t="{t}"><span class="ts">{t}</span><p>{esc(txt)}</p></div>'
        for t, txt in segs)

    toc_html = "".join(f'<a href="#{hid}">{esc(t)}</a>' for t, hid in toc[:14])

    duration = meta.get("audio_seconds") or meta.get("duration") or 0
    meta_bits = []
    if meta.get("author"):
        meta_bits.append(f"UP 主 <b>{esc(meta['author'])}</b>")
    if meta.get("pubdate"):
        meta_bits.append(f"发布 <b>{esc(meta['pubdate'])}</b>")
    if meta.get("bvid"):
        meta_bits.append(f"<b>{esc(meta['bvid'])}</b>")
    meta_html = "".join(f"<li>{b}</li>" for b in meta_bits)
    link_line = f'<li><a href="{esc(meta["url"])}">{esc(meta["url"])}</a></li>' if meta.get("url", "").startswith("http") else ""

    page = f"""<!doctype html>
<html lang="zh-CN" data-theme="dark"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(raw_title)} · 视频讲义</title>
<style>
{CSS}
</style></head><body><div id="bar"></div>
<header class="hero"><div class="wrap">
  <div class="kicker">视频讲义 · 自动生成</div>
  <h1>{esc(title)}</h1>
  <p class="sub">{esc((meta.get('author') or '视频') + ' · ' + human_duration(duration) + ' · 文字稿与拆解')}</p>
  <ul class="meta">{meta_html}{link_line}</ul>
  <div class="stats">
    <div class="st"><div class="v">{human_duration(duration)}</div><div class="k">视频时长</div></div>
    <div class="st"><div class="v">{chars:,}</div><div class="k">逐字稿字数</div></div>
    <div class="st"><div class="v">{len(segs)}</div><div class="k">带时间戳段落</div></div>
    <div class="st"><div class="v">{esc(meta.get('processed_at', '')[:10])}</div><div class="k">生成日期</div></div>
  </div>
</div></header>
<div class="shell">
<nav class="toc"><h6>目录</h6>
  <a href="#analysis">拆解</a>
  {toc_html}
  <a href="#transcript">逐字稿</a>
  <button class="themebtn" id="theme">切换浅色</button>
  <button class="themebtn" id="fsize">字号 100%</button>
</nav>
<main>
  <section id="analysis">
    <div class="sec-head"><span class="sec-no">01</span><h2 class="sec-t">拆解</h2></div>
    {body}
  </section>
  <section id="transcript">
    <div class="sec-head"><span class="sec-no">02</span><h2 class="sec-t">逐字稿</h2></div>
    <div class="note">自动转写，仅做术语机械替换，<strong>未逐句人工校对</strong>。点时间戳可复制。</div>
    <div class="tbar"><input id="q" type="search" placeholder="搜索逐字稿…" autocomplete="off"><span class="count" id="cnt">{len(segs)} 段</span></div>
    <div id="segs">{seg_html}</div>
  </section>
</main>
</div>
<footer><div class="wrap">
  <p>来源：{esc(raw_title)}{' · ' + esc(meta.get('url', '')) if meta.get('url', '').startswith('http') else ''}</p>
  <p>本页为自包含单文件，不依赖网络，可离线打开与打印。逐字稿由 whisper.cpp 自动转写，引用数字请以原视频为准。</p>
</div></footer>
<button id="top">↑</button>
<script>
(function(){{
  var bar=document.getElementById('bar'),top=document.getElementById('top');
  addEventListener('scroll',function(){{
    var h=document.documentElement,s=h.scrollTop,m=h.scrollHeight-h.clientHeight;
    bar.style.width=(m>0?s/m*100:0)+'%'; top.classList.toggle('show',s>700);
  }},{{passive:true}});
  top.onclick=function(){{scrollTo({{top:0,behavior:'smooth'}})}};
  var root=document.documentElement,btn=document.getElementById('theme');
  var saved=localStorage.getItem('vpage-theme');
  if(saved)root.dataset.theme=saved;
  function sync(){{btn.textContent=root.dataset.theme==='dark'?'切换浅色':'切换深色';}}sync();
  btn.onclick=function(){{root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';localStorage.setItem('vpage-theme',root.dataset.theme);sync();}};
  var links=[].slice.call(document.querySelectorAll('nav.toc a'));
  var secs=links.map(function(a){{return document.querySelector(a.getAttribute('href'));}});
  function spy(){{
    var y=scrollY+180, idx=0;
    for(var i=0;i<secs.length;i++){{
      if(!secs[i]) continue;
      var t=secs[i].getBoundingClientRect().top+scrollY;
      if(t<=y) idx=i;
    }}
    links.forEach(function(l,i){{ l.classList.toggle('on', i===idx); }});
  }}
  addEventListener('scroll',spy,{{passive:true}}); spy();
  var fs=document.getElementById('fsize'), sizes=[19.5,21,22.5], fidx=0;
  var savedFs=parseInt(localStorage.getItem('vpage-fs')||'0',10);
  if(savedFs>=0 && savedFs<sizes.length) fidx=savedFs;
  function applyFs(){{ root.style.fontSize=sizes[fidx]+'px'; fs.textContent='字号 '+Math.round(sizes[fidx]/19.5*100)+'%'; }}
  applyFs();
  fs.addEventListener('click',function(){{ fidx=(fidx+1)%sizes.length; localStorage.setItem('vpage-fs',fidx); applyFs(); }});
  var q=document.getElementById('q'),cnt=document.getElementById('cnt');
  var segs=[].slice.call(document.querySelectorAll('.seg'));
  var raws=segs.map(function(s){{return s.querySelector('p').textContent}});
  var total=segs.length,t;
  function esc(s){{return s.replace(/[&<>]/g,function(c){{return {{'&':'&amp;','<':'&lt;','>':'&gt;'}}[c]}})}};
  q.addEventListener('input',function(){{
    clearTimeout(t);t=setTimeout(function(){{
      var k=q.value.trim().toLowerCase();
      if(!k){{segs.forEach(function(s,i){{s.hidden=false;s.querySelector('p').innerHTML=raws[i]}});cnt.textContent=total+' 段';return;}}
      var n=0;
      segs.forEach(function(s,i){{
        var hit=raws[i].toLowerCase().indexOf(k)>=0;s.hidden=!hit;
        if(hit){{n++;var idx=raws[i].toLowerCase().indexOf(k),node=s.querySelector('p');
          node.innerHTML=esc(raws[i].slice(0,idx))+'<mark>'+esc(raws[i].slice(idx,idx+k.length))+'</mark>'+esc(raws[i].slice(idx+k.length));}}
      }});
      cnt.textContent=n+' / '+total+' 段';
    }},120);
  }});
  document.getElementById('segs').addEventListener('click',function(e){{
    var ts=e.target.closest('.ts');if(!ts)return;
    navigator.clipboard&&navigator.clipboard.writeText(ts.textContent);
    var o=ts.textContent;ts.textContent='已复制';setTimeout(function(){{ts.textContent=o}},800);
  }});
}})();
</script></body></html>"""

    out_path = os.path.join(proj, args.out)
    open(out_path, "w", encoding="utf-8").write(page)
    print(f"[page] {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB, {len(toc)} 个二级标题)")


if __name__ == "__main__":
    main()
