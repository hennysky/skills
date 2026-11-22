#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""转写：audio16k.wav → transcript.srt / transcript.md / segments.json

用法:
  python3 transcribe.py <项目目录> [--model PATH] [--language zh] [--threads 8]

依赖：whisper-cli（brew install whisper-cpp）+ GGML 模型
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL = os.path.expanduser("~/models/whisper/ggml-large-v3-turbo.bin")


def die(msg):
    print(f"[asr] 错误：{msg}", file=sys.stderr)
    sys.exit(2)


def find_cli():
    for p in (shutil.which("whisper-cli"), "/opt/homebrew/bin/whisper-cli", "/usr/local/bin/whisper-cli"):
        if p and os.path.exists(p):
            return p
    die("找不到 whisper-cli。安装：brew install whisper-cpp")


def find_model(explicit):
    for p in (explicit, os.environ.get("WHISPER_MODEL"), DEFAULT_MODEL):
        if p and os.path.exists(p):
            return p
    die("找不到模型。下载：\n"
        "  mkdir -p ~/models/whisper && curl -L -o ~/models/whisper/ggml-large-v3-turbo.bin \\\n"
        "  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin")


def parse_srt(path):
    raw = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    segs = []
    for block in re.split(r"\n\s*\n", raw.strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        tl = [l for l in lines if "-->" in l]
        if not tl:
            continue
        h, m, s, ms = re.findall(r"\d+", tl[0])[:4]
        t = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
        text = "".join(lines[lines.index(tl[0]) + 1:]).strip()
        if text:
            segs.append((t, text))
    return segs


def load_glossary(project):
    pairs = []
    for p in (os.path.join(SKILL_DIR, "glossary", "zh-common.txt"),
              os.path.join(project, "glossary.txt")):
        if not os.path.exists(p):
            continue
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=>" not in line:
                continue
            a, b = line.split("=>", 1)
            pairs.append((a.strip(), b.strip()))
    return pairs


def ts(sec):
    sec = int(sec)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def build_paragraphs(segs):
    paras, cur, start, last = [], [], None, None
    for t, text in segs:
        if start is None:
            start = t
        if last is not None and (t - last > 3.5 or sum(len(x) for x in cur) > 220):
            paras.append((start, "".join(cur)))
            cur, start = [], t
        cur.append(text)
        last = t
    if cur:
        paras.append((start, "".join(cur)))
    return paras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--model", default=None)
    ap.add_argument("--language", default="zh")
    ap.add_argument("--threads", type=int, default=max(4, (os.cpu_count() or 8) // 2))
    ap.add_argument("--clean-audio", action="store_true", help="转写成功后删除 audio16k.wav")
    args = ap.parse_args()

    proj = os.path.abspath(args.project)
    wav = os.path.join(proj, "audio16k.wav")
    if not os.path.exists(wav):
        die(f"缺少 {wav}，先跑 fetch.py")

    cli, model = find_cli(), find_model(args.model)
    out = os.path.join(proj, "asr")
    t0 = time.time()
    print(f"[asr] {cli.split('/')[-1]} · {os.path.basename(model)} · {args.threads} 线程")
    subprocess.run([cli, "-m", model, "-f", wav, "-l", args.language,
                    "-otxt", "-osrt", "-oj", "-of", out,
                    "-t", str(args.threads), "-bs", "5", "-pp"], check=True)
    print(f"[asr] 转写完成，用时 {time.time() - t0:.0f}s")

    srt = out + ".srt"
    if not os.path.exists(srt):
        die("whisper 没有产出 srt")
    shutil.copy(srt, os.path.join(proj, "transcript.srt"))

    segs = parse_srt(srt)
    glossary = load_glossary(proj)

    def fix(text):
        for a, b in glossary:
            text = text.replace(a, b)
        return text

    paras = build_paragraphs(segs)
    meta = json.load(open(os.path.join(proj, "meta.json"), encoding="utf-8"))
    chars = sum(len(t) for _, t in paras)

    head = [
        "# 逐字稿",
        "",
        f"> 来源：{meta.get('title', '')}"
        + (f" · {meta.get('author')}" if meta.get("author") else "")
        + (f" · {meta.get('url')}" if meta.get("url") else ""),
        f"> 生成：{time.strftime('%Y-%m-%d')} · whisper.cpp · 用时约 {time.time() - t0:.0f} 秒",
        "> 说明：自动转写，仅做术语机械替换，未逐句人工校对；时间戳为该段起始时间。",
        "",
    ]
    body = [f"**[{ts(t)}]** {fix(txt)}\n" for t, txt in paras]
    open(os.path.join(proj, "transcript.md"), "w", encoding="utf-8").write(
        "\n".join(head + body))

    json.dump([{"t": ts(t), "sec": round(t, 1), "text": fix(txt)} for t, txt in paras],
              open(os.path.join(proj, "segments.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    meta["transcript"] = {"segments": len(paras), "chars": chars,
                          "last_ts": ts(segs[-1][0]) if segs else None,
                          "raw_segments": len(segs)}
    json.dump(meta, open(os.path.join(proj, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    if args.clean_audio and os.path.exists(wav):
        os.remove(wav)
        print("[asr] 已删除 audio16k.wav（--clean-audio）")
    print(f"[asr] {len(paras)} 段 / {chars} 字 / 结束于 {ts(segs[-1][0]) if segs else '-'}")
    print(os.path.join(proj, "transcript.md"))


if __name__ == "__main__":
    main()
