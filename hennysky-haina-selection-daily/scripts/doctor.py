#!/usr/bin/env python3
"""haina-selection MCP 自检：确认 skill 的数据源是否就绪。

用法:
    python3 doctor.py

检查三件事:
    1. mcp.json 里有没有 haina-selection 条目
    2. 条目配置是否完整（type/url/Authorization）
    3. 能否连通 MCP server（列出工具）

退出码: 0 = 全部通过; 1 = 未就绪（会打印具体缺什么和怎么补）

注意: 本脚本只读取本地凭证用于探活，绝不会打印 token，也不上传任何东西。
"""

import json
import os
import sys
import urllib.request
import urllib.error

MCP_NAME = "haina-selection"
MCP_JSON_CANDIDATES = [
    os.path.expanduser("~/.workbuddy/mcp.json"),
    os.path.expanduser("~/.workbuddy/.mcp.json"),
]


def find_mcp_json():
    for p in MCP_JSON_CANDIDATES:
        if os.path.isfile(p):
            return p
    return None


def probe(url, headers, timeout=15):
    """用 initialize 请求探活，成功返回工具数量，失败返回错误信息。"""
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "haina-doctor", "version": "1.0"},
        },
    }).encode("utf-8")
    hdrs = {"Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"}
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=body, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
        # streamableHttp 可能返回 SSE 格式，取 data: 行
        if raw.lstrip().startswith("event:") or "data:" in raw[:200]:
            for line in raw.splitlines():
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    break
        obj = json.loads(raw)
        if isinstance(obj, dict) and obj.get("result"):
            return True, "MCP 握手成功（服务端已响应）"
        if isinstance(obj, dict) and "error" in obj:
            return False, f"服务端返回错误: {obj['error']}"
        return False, f"响应格式异常: {raw[:120]}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} {e.reason}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    print(f"=== {MCP_NAME} 自检 ===\n")

    cfg_path = find_mcp_json()
    if not cfg_path:
        print("[FAIL] 没找到 MCP 配置文件。")
        print("       期望位置: ~/.workbuddy/mcp.json")
        print("       按 references/mcp-setup.md 的步骤创建并配置。")
        sys.exit(1)
    print(f"[OK] 找到配置文件: {cfg_path}")

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"[FAIL] mcp.json 解析失败: {e}")
        sys.exit(1)

    servers = cfg.get("mcpServers", {})
    entry = servers.get(MCP_NAME)
    if not entry:
        print(f"[FAIL] mcp.json 里没有 '{MCP_NAME}' 这一项。")
        print(f"       当前已配置的 MCP: {', '.join(servers.keys()) or '(空)'}")
        print("       按 references/mcp-setup.md 把 haina-selection 加进去。")
        sys.exit(1)
    print(f"[OK] mcp.json 里已配置 '{MCP_NAME}'")

    url = entry.get("url")
    if not url:
        print("[FAIL] haina-selection 缺少 url 字段。")
        sys.exit(1)
    headers = entry.get("headers", {})
    has_auth = any(k.lower() == "authorization" for k in headers)
    masked_url = url[:45] + ("..." if len(url) > 45 else "")
    print(f"[OK] url = {masked_url}")
    print(f"[{'OK' if has_auth else 'WARN'}] Authorization header "
          f"{'存在' if has_auth else '缺失（可能需要，看服务端要求）'}")

    ok, msg = probe(url, headers)
    if ok:
        print(f"[OK] {msg}")
    else:
        print(f"[FAIL] 连不上 MCP server: {msg}")
        print("       可能原因: 地址写错 / token 失效 / 网络不通 / 服务端没启动。")
        sys.exit(1)

    print("\n=== 全部通过：haina-selection 已就绪 ===")
    print("提醒: MCP 配置改过之后，需要在 WorkBuddy 连接器管理页点「信任」并重启客户端才会生效。")


if __name__ == "__main__":
    main()
