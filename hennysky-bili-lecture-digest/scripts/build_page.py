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
    s = re.sub(r"(?<![=&]) = (?![=>])", ' <span class="eq">=</span> ', s)
    s = re.sub(r"(?<!\s)=(?!=)", ' <span class="eq">=</span> ', s)
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
<html lang="zh-CN" data-theme="light"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(raw_title)} · 视频讲义</title>
<style>
:root{{--paper:#fbf8f3;--ink:#1c1a17;--muted:#6f675b;--line:#e6ded1;--card:#fffdf9;--accent:#a8402a;--accent2:#2c5f63;--mark:#ffe9a8}}
html[data-theme=dark]{{--paper:#14130f;--ink:#ece5d8;--muted:#9c9486;--line:#2d2922;--card:#1b1a15;--accent:#e0805f;--accent2:#7fb3b0;--mark:#6b5a1e}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--paper);color:var(--ink);font:16.5px/1.9 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",sans-serif;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent2);text-underline-offset:3px}}
code{{font:.88em ui-monospace,Menlo,monospace;background:rgba(127,127,127,.12);padding:.12em .38em;border-radius:4px;overflow-wrap:anywhere}}
#bar{{position:fixed;top:0;left:0;height:2px;width:0;background:var(--accent);z-index:99}}
.hero{{border-bottom:1px solid var(--line);padding:64px 0 30px;background:radial-gradient(1200px 300px at 12% -10%,rgba(168,64,42,.06),transparent 60%)}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 30px}}
.kicker{{font-size:12px;letter-spacing:.22em;color:var(--accent);margin-bottom:18px}}
h1{{font-family:"Songti SC","Noto Serif SC",Georgia,serif;font-size:clamp(32px,5vw,52px);line-height:1.18;margin:0 0 14px;font-weight:600}}
.sub{{font-family:"Songti SC",serif;font-size:clamp(16px,2vw,20px);color:var(--muted);margin:0 0 26px}}
.meta{{display:flex;flex-wrap:wrap;gap:8px 24px;font-size:13.5px;color:var(--muted);margin:0;padding:0;list-style:none}}
.meta b{{color:var(--ink);font-weight:600}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden;margin:30px 0 0}}
.st{{background:var(--card);padding:15px 18px}}
.st .v{{font-family:"Songti SC",serif;font-size:25px}}
.st .k{{font-size:12px;color:var(--muted);margin-top:3px}}
.shell{{display:grid;grid-template-columns:200px minmax(0,1fr);gap:58px;max-width:1100px;margin:0 auto;padding:44px 30px 90px}}
nav.toc{{position:sticky;top:26px;align-self:start;font-size:13.5px;max-height:calc(100vh - 50px);overflow:auto}}
nav.toc h6{{font-size:11px;letter-spacing:.2em;color:var(--muted);margin:0 0 12px}}
nav.toc a{{display:block;color:var(--muted);text-decoration:none;padding:5px 0 5px 12px;border-left:2px solid transparent;line-height:1.5}}
nav.toc a:hover{{color:var(--ink)}}nav.toc a.on{{color:var(--accent);border-left-color:var(--accent);font-weight:600}}
.themebtn{{margin-top:22px;font:12px inherit;color:var(--muted);background:none;border:1px solid var(--line);border-radius:20px;padding:6px 12px;cursor:pointer}}
main{{min-width:0}}
section{{margin-bottom:70px;scroll-margin-top:24px;min-width:0}}
.sec-head{{display:flex;align-items:baseline;gap:14px;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:26px}}
.sec-no{{font-family:"Songti SC",serif;font-size:13px;color:var(--accent);letter-spacing:.14em}}
h2.sec-t{{font-family:"Songti SC",serif;font-size:clamp(24px,3.2vw,30px);margin:0;font-weight:600}}
h2{{font-family:"Songti SC",serif;font-size:22px;margin:40px 0 12px;font-weight:600;line-height:1.45;scroll-margin-top:20px}}
h3{{font-family:"Songti SC",serif;font-size:18.5px;margin:30px 0 8px}}
h4{{font-size:16px;margin:24px 0 8px}}
p{{margin:0 0 14px}}ul,ol{{margin:0 0 16px;padding-left:22px}}li{{margin:5px 0}}
hr{{border:0;border-top:1px solid var(--line);margin:28px 0}}
.note{{border-left:3px solid var(--accent);background:rgba(168,64,42,.05);padding:12px 16px;border-radius:0 8px 8px 0;color:var(--muted);font-size:15px;margin:0 0 20px}}
pre{{background:rgba(127,127,127,.08);padding:14px 16px;border-radius:10px;overflow:auto;font-size:12.5px;line-height:1.7;border:1px solid var(--line);min-width:0;max-width:100%}}
.tw{{overflow-x:auto;margin:0 0 20px;border:1px solid var(--line);border-radius:10px;min-width:0;max-width:100%}}
table{{border-collapse:collapse;width:100%;font-size:14.5px;min-width:480px}}
th,td{{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:rgba(127,127,127,.06);font-weight:600;font-size:13px;white-space:nowrap}}
tbody tr:last-child td{{border-bottom:0}}
.formula{{display:flex;justify-content:center;align-items:center;margin:6px 0 20px;padding:14px 10px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);font-family:"Times New Roman",serif;font-size:21px;overflow-x:auto}}
.formula .frac{{display:inline-flex;flex-direction:column;text-align:center;vertical-align:middle;margin:0 5px;line-height:1.25}}
.formula .frac .n{{border-bottom:1.2px solid currentColor;padding:0 5px 2px}}
.formula .frac .d{{padding:2px 5px 0}}
.formula .rad .rb{{border-top:1.2px solid currentColor;padding:0 3px;margin-left:1px}}
sub,sup{{font-size:.68em;line-height:0}}
.tbar{{position:sticky;top:0;z-index:5;background:var(--paper);padding:12px 0;display:flex;gap:12px;align-items:center;border-bottom:1px solid var(--line);margin-bottom:8px}}
.tbar input{{flex:1;min-width:0;font:14px inherit;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 13px;outline:none}}
.tbar input:focus{{border-color:var(--accent2)}}
.tbar .count{{font-size:12.5px;color:var(--muted);white-space:nowrap}}
.seg{{display:grid;grid-template-columns:58px minmax(0,1fr);gap:16px;padding:11px 0;border-bottom:1px dashed var(--line)}}
.seg[hidden]{{display:none}}
.seg .ts{{font:12px/1.9 ui-monospace,Menlo,monospace;color:var(--accent2);opacity:.75;padding-top:3px;cursor:copy}}
.seg p{{margin:0;font-size:15.5px;line-height:1.95}}
.seg mark{{background:var(--mark);color:inherit}}
footer{{border-top:1px solid var(--line);padding:30px 0 60px;color:var(--muted);font-size:13px}}
#top{{position:fixed;right:24px;bottom:24px;width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:var(--card);color:var(--muted);cursor:pointer;display:none}}
#top.show{{display:block}}
@media (max-width:900px){{
  html,body{{overflow-x:clip}}
  .shell{{grid-template-columns:minmax(0,1fr);gap:0;padding-top:26px}}
  nav.toc{{position:static;max-height:none;margin-bottom:30px;border-bottom:1px solid var(--line);padding-bottom:14px}}
  nav.toc a{{display:inline-block;border-left:0;border-bottom:2px solid transparent;padding:4px 10px 4px 0}}
  nav.toc a.on{{border-left:0;border-bottom-color:var(--accent)}}
  .st:last-child{{grid-column:1/-1}}
}}
@media print{{nav.toc,.tbar,#top,#bar,.themebtn{{display:none!important}}.shell{{grid-template-columns:1fr;padding:0}}body{{font-size:11.5pt}}table,.formula{{page-break-inside:avoid}}}}
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
  <button class="themebtn" id="theme">切换深色</button>
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
  if('IntersectionObserver' in window){{
    var io=new IntersectionObserver(function(es){{es.forEach(function(e){{
      if(e.isIntersecting){{links.forEach(function(l){{l.classList.remove('on')}});var i=secs.indexOf(e.target);if(i>=0)links[i].classList.add('on');}}
    }})}},{{rootMargin:'-12% 0px -75% 0px'}});
    secs.forEach(function(s){{if(s)io.observe(s)}});
  }}
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
