#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取音频：B 站链接 / BV 号 / 本地文件 → 项目目录（meta.json + audio16k.wav）

用法:
  python3 fetch.py <url|BV号|文件路径> [--out DIR] [--max-seconds N] [--keep]

只读、无第三方依赖（urllib + hashlib + subprocess）。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
REFERER = "https://www.bilibili.com/"
MIXIN_TAB = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
             33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61,
             26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36,
             20, 34, 44, 52]


def die(msg, code=2):
    print(f"[fetch] 错误：{msg}", file=sys.stderr)
    sys.exit(code)


def info(msg):
    print(f"[fetch] {msg}")


def http_get(url, timeout=25, referer=None, want_json=True):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Referer": referer or REFERER,
        "Accept": "application/json, */*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if want_json else raw


def resolve_target(target):
    """返回 (bvid, url)。本地文件返回 (None, path)。"""
    if os.path.exists(target):
        return None, os.path.abspath(target)
    url = target
    if "b23.tv" in target or "bili2233" in target:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            url = r.geturl()
    m = re.search(r"(BV[0-9A-Za-z]{10})", url)
    if m:
        bvid = m.group(1)
        canon = url.split("?")[0] if url.startswith("http") else f"https://www.bilibili.com/video/{bvid}"
        return bvid, canon
    m = re.search(r"av(\d+)", url)
    if m:
        return f"av{m.group(1)}", url.split("?")[0]
    die(f"认不出这个链接：{target}")


def wbi_sign(params):
    nav = http_get("https://api.bilibili.com/x/web-interface/nav")
    img = nav["data"]["wbi_img"]["img_url"].split("/")[-1].split(".")[0]
    sub = nav["data"]["wbi_img"]["sub_url"].split("/")[-1].split(".")[0]
    raw = img + sub
    mixin = "".join(raw[i] for i in MIXIN_TAB)[:32]
    p = dict(params, wts=int(time.time()))
    q = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v).replace(chr(33), '').replace(chr(39), '').replace('(', '').replace(')', '').replace('*', ''), safe='')}"
        for k, v in sorted(p.items())
    )
    return q + "&w_rid=" + hashlib.md5((q + mixin).encode()).hexdigest()


def pick_audio(dash):
    audios = dash.get("audio") or []
    if not audios:
        return None
    return sorted(audios, key=lambda a: -a.get("bandwidth", 0))[0]["baseUrl"]


def download(url, out_wav, max_seconds=None):
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-user_agent", UA, "-headers", f"Referer: {REFERER}\r\n",
           "-i", url]
    if max_seconds:
        cmd += ["-t", str(max_seconds)]
    cmd += ["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", out_wav]
    subprocess.run(cmd, check=True)


def ffmpeg_duration(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
        return round(float(out.stdout.strip()), 1)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out", help="项目目录（默认 projects/<slug>）")
    ap.add_argument("--max-seconds", type=int, help="只取前 N 秒（测试用）")
    ap.add_argument("--keep", action="store_true", help="保留下载的中间文件")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"缺少 {tool}。安装：brew install ffmpeg（装完再跑一次）")
    bvid, url = resolve_target(args.target)
    is_local = bvid is None
    meta = {}

    if is_local:
        slug = re.sub(r"[^\w\-]+", "-", os.path.splitext(os.path.basename(url))[0])[:40]
        meta = {"title": os.path.basename(url), "source": "local", "path": url, "url": url}
        duration = ffmpeg_duration(url)
        meta["duration"] = duration
        info(f"本地文件：{url}（{duration}s）")
    else:
        info(f"视频：{bvid}，取元数据…")
        view = http_get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}")
        if view.get("code") != 0:
            die(f"view 接口失败：{view.get('code')} {view.get('message')}")
        d = view["data"]
        cid = d["pages"][0]["cid"]
        meta = {
            "title": d["title"],
            "bvid": bvid,
            "cid": cid,
            "url": url,
            "author": d["owner"]["name"],
            "pubdate": time.strftime("%Y-%m-%d", time.localtime(d["pubdate"])),
            "duration": d["duration"],
            "source": "bilibili",
        }
        info(f"{d['title']} · {d['owner']['name']} · {d['duration']}s")

    out_dir = args.out or os.path.join("projects", (meta.get("bvid") or slug))
    os.makedirs(out_dir, exist_ok=True)
    wav = os.path.join(out_dir, "audio16k.wav")

    if is_local:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", url,
                        "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav], check=True)
    else:
        aurl = None
        try:
            qs = wbi_sign({"bvid": bvid, "cid": meta["cid"], "fnval": "16", "fnver": "0", "fourk": "1"})
            play = http_get(f"https://api.bilibili.com/x/player/wbi/playurl?{qs}")
            if play.get("code") == 0:
                dash = play["data"].get("dash") or {}
                aurl = pick_audio(dash)
                if not aurl and play["data"].get("durl"):
                    aurl = play["data"]["durl"][0]["url"]
        except Exception as e:
            info(f"WBI 取流失败（{type(e).__name__}），尝试 yt-dlp 兜底…")

        if aurl:
            info("下载并转码…")
            download(aurl, wav, args.max_seconds)
        else:
            if not shutil.which("yt-dlp"):
                die("取流失败，且本机没有 yt-dlp。安装：brew install yt-dlp")
            info("用 yt-dlp 兜底下载…")
            cmd = ["yt-dlp", "-f", "bestaudio", "--no-playlist", "-o", os.path.join(out_dir, "audio.%(ext)s"), url]
            subprocess.run(cmd, check=True)
            src = next((os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("audio.") and not f.endswith(".wav")), None)
            if not src:
                die("yt-dlp 没有产出音频文件")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "16000",
                            "-c:a", "pcm_s16le"] + (["-t", str(args.max_seconds)] if args.max_seconds else []) + [wav], check=True)

    if not os.path.exists(wav):
        die("没有生成 audio16k.wav")

    got = ffmpeg_duration(wav)
    meta["audio_seconds"] = got
    if args.max_seconds:
        meta["truncated_to"] = args.max_seconds
    meta["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    info(f"完成：{out_dir}/  （音频 {got}s）")
    print(os.path.abspath(out_dir))


if __name__ == "__main__":
    main()
