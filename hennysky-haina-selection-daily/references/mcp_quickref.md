# haina-selection MCP 速查

## 连接方式

`haina-selection` 是用户自定义的 `streamableHttp` MCP，配置在 `~/.workbuddy/mcp.json`。它**不在**官方连接器列表里，`list_installed_plugins` 查不到；直接用 ToolSearch 加载下列工具名，再用 DeferExecuteTool 调用。

配置形如：
```json
"haina-selection": {
  "type": "streamableHttp",
  "url": "...",
  "headers": {"Authorization": "Bearer ..."},
  "timeout": 60000
}
```
若连不上，先读 `~/.workbuddy/mcp.json` 确认条目是否还在，不要去 `list_installed_plugins` 找。

## 五个工具

### stats
看入库总量和最新批次时间。无参数。返回 `batches`（批次数）、`items`（条目数）、`last`（最新批次名和时间）。用于报告头部统计。

### list_days
列出有采集数据的日期，新的在前。参数：`limit`（整数，默认 30）。
用户问「最近有什么」「昨天有什么」时**先调这个**，不要直接猜日期。

### get_items
按日期拉当天新品清单，是日报主数据源。参数：
- `date`（字符串 `YYYY-MM-DD`，不传则用最新一天）
- `platform`（平台名，如 Minted / Wayfair）
- `min_price` / `max_price`（数字，美元）
- `keyword`（在标题里搜索）
- `limit`（默认 50，日报要调大到 200）

返回 `items` 数组，每款字段：
`id`（如 S601）、`platform`、`title`、`title_cn`、`artist`、`price_usd`、`size_in`、`reviews`、`url`、`image_url`、`image_note`、`evidence`、`overlap_with_catalog`、`analysis`。

另有 `sources` 数组，记录每个平台的抓取状态（`status`: ok/failed）、`http_status`、`count`、`note`。**失败原因从这里读**，写日报「数据坑」一节要用。

### get_item
看单款完整资料（证据说明、模型分析、图片、商品页）。参数：`id`（必填，如 S601）、`date`（不传则最近 30 天找）。用户单独问某一款时用。

### ingest_batch
批量入库。参数复杂，日报流程用不到；只有用户明确要「把数据存进去」时才查 schema。

### export_zip
导出压缩包。用户说「导出全部数据」时用。

## 已知陷阱（实测）

1. **Etsy 价格置空**：Etsy 页面显示日元不是美元，系统按规则把 `price_usd` 置为 `null`，不是抓取失败。报告里注明「价格按规则置空，需人工补」，不要写成「没抓到」。
2. **Etsy 尺寸缺失**：同理，未选具体变体时 `size_in` 为 `null`。
3. **analysis 不可信**：`analysis._model` 通常是 `deepseek-chat`，`_vision` 为 `false`——模型没看到图，只凭标题和价格推断。约一半条目会出现「画面看不清」「不确定」。**必须看图后纠正**，详见 `judging_rules.md`。
4. **图片缺失的三种情况**：
   - Minted：`image_url` 为 null，`image_note` 写明「平台图片不让程序下载，得人工打开商品页看」。
   - Saatchi Art：抓取超时，`image_note` 写明超时。
   - 其他平台偶尔缺图，看 `image_note`。
   这些款在报告里单列「没抓到图的 N 款」，不要硬凑结论。
5. **CB2 图是缩略图**：能看出大致风格和配色，但细节判不清，报告里要标注「缩略图，需拿高清图」。
6. **reviews 为 null**：Society6 的聚合评论跨多个设计，未逐产品核实，故置空。
7. **evidence 里的「第None位」**：抓取时排名序号没拿到，属于已知数据缺口，不影响选品判断。
8. **日期以库为准**：用户说「今天」时，先 `list_days` 确认库里最新日期；若最新不是今天，用最新日期并在报告里写明实际日期。
