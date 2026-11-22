#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境自检：这个技能在这台电脑上能不能跑。

用法:
  python3 doctor.py

输出每一项 PASS / MISSING，最后给一句结论。退出码 0 = 可跑。
"""
import os
import shutil
import sys

OK, BAD, WARN = "PASS", "MISSING", "WARN"
rows = []


def add(status, name, detail, fix=""):
    rows.append((status, name, detail, fix))


def which_any(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


# Python
py = sys.version_info
add(OK if py >= (3, 8) else BAD, "Python",
    f"{py.major}.{py.minor}.{py.micro}",
    "macOS 自带没有 python3：xcode-select --install 或 brew install python")

# ffmpeg / ffprobe
for tool, pkg in (("ffmpeg", "ffmpeg"), ("ffprobe", "ffmpeg")):
    p = which_any(tool)
    add(OK if p else BAD, tool, p or "未找到", f"brew install {pkg}")

# whisper-cli
cli = which_any("whisper-cli") or next(
    (p for p in ("/opt/homebrew/bin/whisper-cli", "/usr/local/bin/whisper-cli") if os.path.exists(p)), None)
add(OK if cli else BAD, "whisper-cli", cli or "未找到", "brew install whisper-cpp")

# 模型
model = (os.environ.get("WHISPER_MODEL")
         or os.path.expanduser("~/models/whisper/ggml-large-v3-turbo.bin"))
if os.path.exists(model):
    gb = os.path.getsize(model) / 1024 ** 3
    add(OK if gb > 0.5 else WARN, "ASR 模型", f"{model}（{gb:.1f} GB）")
else:
    add(BAD, "ASR 模型", f"未找到 {model}",
        "curl -L -o ~/models/whisper/ggml-large-v3-turbo.bin "
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin")

# 可选：yt-dlp 兜底
yt = which_any("yt-dlp")
add(OK if yt else WARN, "yt-dlp（可选）", yt or "未装，B 站签名失效时无法兜底", "brew install yt-dlp")

# 磁盘
du = shutil.disk_usage(os.path.expanduser("~"))
free_gb = du.free / 1024 ** 3
add(OK if free_gb > 5 else WARN, "剩余磁盘", f"{free_gb:.0f} GB（每段 1 小时视频约 112 MB 中间文件）")

print("\n视频转讲义 · 环境自检\n" + "-" * 46)
for st, name, detail, fix in rows:
    print(f"[{st:6}] {name:14} {detail}")
    if st != OK and fix:
        print(f"          → {fix}")
fails = sum(1 for r in rows if r[0] == BAD)
print("-" * 46)
if fails == 0:
    print("结论：可以跑。先拿 5 分钟片段验证：")
    print('  python3 scripts/fetch.py "BV号" --out ~/Desktop/讲义/test --max-seconds 300')
else:
    print(f"结论：还差 {fails} 项，按上面的 → 装完再跑一次 doctor.py")
sys.exit(0 if fails == 0 else 1)
