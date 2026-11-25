# 给 Agent：MCP 没装时的处理指引

## 什么时候会用到

用户说「跑选品日报」，但 ToolSearch 搜不到 `mcp__haina-selection__*` 工具，或调用报「工具不存在 / 服务不可用」。此时**不要简单报错说跑不了**，按下面流程引导。

## Step 1 · 先自检

运行：
```bash
python3 <skill目录>/scripts/doctor.py
```

脚本检查 mcp.json 里有没有 `haina-selection` 条目、配置是否完整、能否连通。它只读本地配置探活，**不打印 token、不上传任何东西**。

## Step 2 · 按 doctor 结果分流

| doctor 输出 | 含义 | 怎么处理 |
|---|---|---|
| `没找到 mcp.json` | 本机从没配过自定义 MCP | 走下方「首次配置」 |
| `mcp.json 里没有 haina-selection` | 配过别的 MCP，但没有这个 | 走下方「首次配置」 |
| `缺少 url / Authorization` | 配置不完整 | 提示用户补全对应字段 |
| `连不上 MCP server` | 网络/token/服务端问题 | 提示检查地址、token 是否过期、服务端是否在线 |
| `全部通过` | 已就绪 | 直接跑日报流程；若工具仍搜不到，提示用户重启 WorkBuddy 并信任该 MCP |

## 首次配置：需要用户提供的两样东西

这个 MCP 是内部服务，**skill 仓库里不放地址里的密钥和 Bearer token**（公开仓库，严禁提交凭证）。所以需要用户从管理员那里拿到：

1. **MCP 地址**（形如 `http://<ip>:<port>/xxx/mcp` 或 `https://.../mcp`）
2. **Bearer token**（一串密钥，用于 `Authorization` header）

告诉用户：「这个 skill 需要一个叫 haina-selection 的数据源，得先拿到服务地址和访问密钥。你找管理员要这两个，我帮你配好，全程不用你懂技术。」

## 配置方法（拿到地址和 token 后）

配置文件是 `~/.workbuddy/mcp.json`（注意不是 `.mcp.json`）。把下面这段加进 `mcpServers`，**保留文件里已有的其它 MCP，不要覆盖**：

```json
{
  "mcpServers": {
    "haina-selection": {
      "type": "streamableHttp",
      "url": "用户提供的地址",
      "headers": {
        "Authorization": "Bearer 用户提供的token"
      },
      "timeout": 60000
    }
  }
}
```

用 Read 读现有文件 → 合并新条目 → Write 写回。不要让用户手改 JSON。

## 配置完的两步（关键，容易漏）

1. **信任 MCP**：在 WorkBuddy 左下角连接器管理页，打开自定义连接器入口，找到新加的 `haina-selection`，点「信任 / 启用」。新加的 MCP 不会自动生效。
2. **重启客户端**：重启 WorkBuddy 后 ToolSearch 才能搜到 `mcp__haina-selection__*` 工具。

然后重跑 `doctor.py`，全部通过即就绪。

## 安全红线

- **绝不**把真实 url 里的密钥路径、Bearer token 写进任何会被提交到 Git 的文件（SKILL.md、references、脚本、示例报告都不行）。
- 示例和文档里一律用占位符：`"url": "用户提供的地址"`、`"Bearer 用户提供的token"`。
- 用户的 token 只存在于他本机的 `~/.workbuddy/mcp.json`，那是他自己的私有配置，不进仓库。
- doctor.py 打印 url 时做了截断，且从不打印 token。
