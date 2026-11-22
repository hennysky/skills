#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抽帧：从视频流/本地视频里每 N 秒取一帧，供阅读 PPT 或屏幕共享内容。

用法:
  python3 frames.py <项目目录> [--url AUDIO_OR_VIDEO_URL] [--every 10] [--width 852]

如果项目里没有视频文件，需要传入 B 站视频流地址（可用 fetch.py 的元数据重新签名取流）。
抽出的帧在 frames/ 下，用图片查看工具看几张即可确认章节结构。
"""
import argparse
import json
import os
import subprocess
import sys

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--url", help="视频流地址（可选；优先用项目里的 video.*）")
    ap.add_argument("--every", type=int, default=10, help="每 N 秒一帧")
    ap.add_argument("--width", type=int, default=852)
    ap.add_argument("--max-seconds", type=int, default=0)
    args = ap.parse_args()

    proj = os.path.abspath(args.project)
    out = os.path.join(proj, "frames")
    os.makedirs(out, exist_ok=True)

    src = None
    for f in os.listdir(proj):
        if f.startswith("video.") or f.startswith("source."):
            src = os.path.join(proj, f)
            break
    if not src:
        src = args.url
    if not src:
        print("[frames] 需要 --url 或项目内的 video.* 文件", file=sys.stderr)
        sys.exit(2)

    vf = f"fps=1/{args.every},scale={args.width}:-1"
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if src.startswith("http"):
        cmd += ["-user_agent", UA, "-headers", "Referer: https://www.bilibili.com/\r\n"]
    cmd += ["-i", src]
    if args.max_seconds:
        cmd += ["-t", str(args.max_seconds)]
    cmd += ["-vf", vf, "-q:v", "4", os.path.join(out, "f_%04d.jpg")]
    subprocess.run(cmd, check=True)

    n = len([f for f in os.listdir(out) if f.endswith(".jpg")])
    meta_p = os.path.join(proj, "meta.json")
    if os.path.exists(meta_p):
        meta = json.load(open(meta_p, encoding="utf-8"))
        meta["frames"] = {"count": n, "every_seconds": args.every}
        json.dump(meta, open(meta_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[frames] {n} 张 → {out}")


if __name__ == "__main__":
    main()
