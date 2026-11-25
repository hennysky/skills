#!/usr/bin/env python3
"""按 haina-selection 的 items JSON 批量下载新品图。

用法:
    python3 fetch_images.py --items-json <items.json> --out-dir <输出目录>

输入 JSON 兼容两种形式:
    1. get_items 的完整返回: {"ok":true, "items":[...], "sources":[...]}
    2. 直接是 items 数组:    [ {...}, {...} ]

输出:
    - 图片保存为 <out-dir>/<id>.jpg
    - 写出 <out-dir>/manifest.json (每款状态、文件名、失败原因)
    - 标准输出打印摘要
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def load_items(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    raise ValueError("JSON 结构不识别：既不是数组，也没有 items 数组")


def download_one(url, dest, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    with open(dest, "wb") as f:
        f.write(raw)
    return len(raw)


def is_jpeg_or_image(path):
    head = b""
    with open(path, "rb") as f:
        head = f.read(16)
    return head.startswith(b"\xff\xd8") or head.startswith(b"\x89PNG")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items-json", required=True, help="get_items 返回的 JSON 文件路径")
    ap.add_argument("--out-dir", required=True, help="图片输出目录")
    ap.add_argument("--timeout", type=int, default=40, help="单张下载超时秒数")
    args = ap.parse_args()

    items = load_items(args.items_json)
    os.makedirs(args.out_dir, exist_ok=True)

    manifest = []
    ok = skip = fail = 0
    for it in items:
        iid = str(it.get("id", "UNKNOWN"))
        url = it.get("image_url")
        rec = {"id": iid, "title": it.get("title"), "platform": it.get("platform")}

        if not url:
            rec.update(status="no_image",
                       reason=it.get("image_note") or "无 image_url")
            manifest.append(rec)
            skip += 1
            print(f"[跳过] {iid}: 无图 ({rec['reason'][:40]})")
            continue

        dest = os.path.join(args.out_dir, f"{iid}.jpg")
        try:
            size = download_one(url, dest, args.timeout)
            if not is_jpeg_or_image(dest):
                raise ValueError("下载内容不是有效图片")
            rec.update(status="ok", file=f"{iid}.jpg", bytes=size)
            ok += 1
            print(f"[成功] {iid}: {size} bytes -> {iid}.jpg")
        except Exception as e:
            rec.update(status="failed", reason=f"{type(e).__name__}: {e}")
            fail += 1
            print(f"[失败] {iid}: {e}")
            if os.path.exists(dest):
                os.remove(dest)

    manifest_path = os.path.join(args.out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(items), "ok": ok, "no_image": skip,
                   "failed": fail, "items": manifest}, f,
                  ensure_ascii=False, indent=2)

    print(f"\n完成：共 {len(items)} 款，成功 {ok}，无图 {skip}，失败 {fail}")
    print(f"清单：{manifest_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
