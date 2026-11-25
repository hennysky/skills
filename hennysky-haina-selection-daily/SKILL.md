---
name: hennysky-haina-selection-daily
description: 海纳艺术选品日报全流程。当用户说「跑一下今天的选品日报」「新品日报」「看看今天的新品」「抓选品图」「生成看图报告」「选品日报+抓图」等，或要求从海纳 selection 数据库拉取新品数据并产出报告时使用。自动完成：调取 haina-selection MCP 数据 → 生成文字日报 → 批量抓取商品图 → 逐张看图纠正标题推断 → 产出分级看图报告 HTML → 打开预览。适用于亚马逊装饰画选品的每日行情扫描。
agent_created: true
version: 1.1.1
---

# 海纳选品日报（端到端）

## 用途

把「拉数据 → 出日报 → 抓图 → 看图 → 出报告」固化为一条龙。用户说一句话即可跑完全过程，无需中途确认。服务对象是亚马逊装饰画选品，产出物是一份可以直接翻着看的看图报告。

数据源是自定义 MCP `haina-selection`（配置在 `~/.workbuddy/mcp.json`），**不是**官方连接器，不会出现在 `list_installed_plugins` 里。

数据从哪来、每天几点更新、哪些地方会缺、缺了意味着什么——见 `references/system-overview.md`。

## 铁律（先看这三条）

1. **每次先做前置检查（Step 0），确认 MCP 可用再往下跑。** 用户可能装了 skill 但没装 MCP，直接调工具只会失败。没装时按引导流程走，不要简单报错。
2. **必须逐张看图后再下结论。** MCP 里的 `analysis` 字段是 `deepseek-chat` 在未开视觉（`_vision: false`）时只凭标题和价格生成的，错误率很高。所有 verdict 默认都是「观察」，不能直接当结论用。看图后要显式标注「纠正了什么」。
3. **默认全链路，不拆开问。** 用户说「跑日报」= 跑完下面全部步骤直到报告打开。除非用户明确只要文字日报（不要抓图），才在抓图那步停下。
4. **报告里每款都必须能点开对应平台的商品详情页。** 用 items 里的 `url` 字段，让图片、标题、按钮三处都能点；无图款也要有链接。不能只给一张看不出处的图。

## 端到端流程

### Step 0 · 前置检查（MCP 是否就绪）

每次跑日报前先做：

1. 用 ToolSearch 搜 `mcp__haina-selection__stats`。搜得到 → MCP 已挂载，跳到 Step 1。
2. 搜不到 → 运行 `python3 <skill目录>/scripts/doctor.py` 自检，按输出分流。
3. 若 doctor 报「没配 / 配置不全 / 连不上」，走 `references/mcp-setup.md` 的引导：告诉用户需要服务地址和 Bearer token（找管理员要），拿到帮他写进 `~/.workbuddy/mcp.json`，再提醒去连接器页点信任 + 重启 WorkBuddy，重跑 doctor 确认。
4. **安全红线**：仓库和文档里一律用占位符，绝不把真实 token 写进任何文件。详见 `references/mcp-setup.md`。

### Step 1 · 拉取当天数据

用 ToolSearch 加载 `mcp__haina-selection__list_days` / `get_items` / `stats` 的 schema，再用 DeferExecuteTool 调用：

1. `list_days`（limit 10）确认最新有数据的日期。**不要假定是今天**——以库里最新日期为准，并在报告里写明日期。
2. `get_items`（date=该日期，limit=200）拉取完整清单。
3. `stats` 取入库总量和最新批次，用于报告头部。

字段含义、筛选参数、Etsy 日元置空等陷阱见 `references/mcp_quickref.md`。

### Step 2 · 生成文字日报

在对话里直接输出（不要先写文件）：
- **总览**：款数、平台数、哪些平台抓取失败及原因（看 `sources` 字段）。
- **分平台清单表格**：编号 | 中文名 | 价格/尺寸 | 一句话判断。
- **当日信号**：从题材、价格带、评论数里归纳 2~3 条趋势。
- **数据坑提醒**：无图、价格缺失、未开视觉等。

这一步让用户先看到数据，Step 3~6 再深化。

### Step 3 · 批量抓图

把 Step 1 拿到的 items 原样保存为 JSON（例如 `output/新品图/<日期>/items.json`），然后运行脚本：

```bash
python3 <skill目录>/scripts/fetch_images.py \
  --items-json <items.json 路径> \
  --out-dir <输出目录>
```

脚本会跳过无 `image_url` 的条目、下载有地址的图、打印成功/失败清单并写出 `manifest.json`。把无图的款记下来（Minted 平台禁抓、Saatchi 超时是常见原因），报告里单列一节。

### Step 4 · 逐张看图并重新判断

用 ViewImage 逐张打开下载的图，每张问同样的问题：
画面主体 / 构图 / 主色调 / 风格 / 适用场景 / 画面或印刷风险。

然后对照 MCP 的 `analysis` 字段，**逐条纠正明显错误**。判断标准和常见错误案例见 `references/judging_rules.md`。

按五级分类打标：值得跟进 / 谨慎 / 小众 / 常规 / 无图。

### Step 5 · 生成看图报告 HTML

以 `assets/report_template.html` 为骨架（CSS 已写好，含商品链接样式，直接用），填入 Step 4 的逐款结论：
- 头部 pill 统计
- 五个分级区块，每款一张卡片（图 + 编号 + 名称 + 价格尺寸 + 真实画面 + 纠正 + 结论）
- **每款卡片的商品链接**：取该款 `url` 字段，填进三处——`<div class="pic">` 里用 `<a href="url" target="_blank">` 包住图片；标题 `<div class="name">` 只给文字加链接（不要在标题后塞按钮，会错位），改在卡片底部 `why` 之后加整行链接条 `<a class="cardlink" href="url" target="_blank">在 平台名 查看商品页 ↗</a>`；无图款清单行末也加链接。模板注释里有完整写法，照抄即可。
- 无图款清单（同样带商品链接）
- 「看图后最该记住的纠正」对照表

产出路径：`<工作区>/output/新品图/<日期>/看图报告.html`，图片放同目录用相对路径引用，链接用绝对 URL 新标签页打开（`target="_blank" rel="noopener"`）。

### Step 6 · 打开预览并汇报

用 present_files 打开报告。对话里给出简短总结：抓到几张、分了几级、最值得看的 2~4 款、关键纠正 2~4 条。最后可问是否要深挖某一类（如高清图、对比款）。

## 常见变体

- **「只要文字日报」**：执行 Step 1~2 后停止。
- **「把某几款细看」**：直接从 Step 4 开始，只处理指定编号。
- **「昨天/某天的日报」**：Step 1 的 `get_items` 传用户指定日期；若该日无数据，说明并用最新日期替代。
- **「导出全部数据」**：调用 `mcp__haina-selection__export_zip`。

## 资源

- `references/mcp_quickref.md` — MCP 五个工具的参数、返回字段、已知陷阱。
- `references/mcp-setup.md` — **MCP 未装时的处理指引**：自检分流、首次配置、安全红线。
- `references/judging_rules.md` — 五级分类标准、看图检查清单、常见标题推断错误案例、选品风险点。
- `scripts/doctor.py` — MCP 就绪自检（配置文件 / 字段完整 / 连通性），不打印 token。
- `scripts/fetch_images.py` — 按 items JSON 批量下载商品图，输出 manifest。
- `assets/report_template.html` — 报告 HTML 骨架，含全部 CSS 和卡片示例。
