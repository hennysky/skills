---
name: visual-planning
description: "将方案、项目计划和实施交接做成包含原生交互图、可勾选待办及完整正文的独立网页，同时交付 DSH Markdown；也可单独制作架构、流程、时序、数据流、状态、ER、类、树、时间线和耗时图。适用于需要图文一体的方案设计、规划页或可视化实施计划。触发词：可视化规划、visual-planning、画架构图、流程图、时序图、数据流图、ER图、类图、时间线、瀑布图、做规划页、方案可视化、实施计划网页。"
license: MIT
metadata:
  version: "1.1.1"
  author: "hennysky"
---

# 可视化规划

这是完整的独立绘图与规划项目。使用随包提供的 `bin/visualplan.mjs`，不查找其他绘图 Skill，不调用外部安装包。用户可称它为“可视化规划”或 `$visual-planning`。

## 安装与调用路径

- 本包可放在任意目录。文中所有 `<SKILL_ROOT>` 一律指**本 SKILL.md 所在目录的绝对路径**。
- 标准安装位置（WorkBuddy 用户级技能）：`~/.workbuddy/skills/visual-planning`。装好后 `<SKILL_ROOT>` 即该路径。
- 安装后先跑一次自检，全部 `[ok]` 才算可用：

```bash
node <SKILL_ROOT>/bin/visualplan.mjs doctor
```

- 包内已含渲染器、schema、离线字体与图标，**不含 `node_modules`、不需要 `npm install`**；唯一运行前提是 Node.js ≥ 18。
- `finalize` 的 `browser-check` 环节需要本机可用的 Chrome。没有浏览器时仍会正常交付页面文件，但回执会标注该项未验证，交付说明里要如实写出。
- **在 WorkBuddy / Codex 等内置终端里运行时，命令前必须加 `env -u NODE_OPTIONS`。** 否则宿主的 Node 钩子会拦截 `finalize` 写回执时的临时目录清理，报 `removal-quarantine-cleanup-failed`，看起来像生成失败（实际页面已产出）。正确写法：

```bash
env -u NODE_OPTIONS node <SKILL_ROOT>/bin/visualplan.mjs finalize architecture spec.json out.html --quality showcase --out-dir <新目录> --json
```

- 详细安装与排障步骤见包内 `安装说明.md`。

## 选择交付

- 用户要方案、实施计划、流程图加待办或规划网页：默认交付同一页面里的原生交互图、完整实施正文和可勾选清单，同时保存独立 DSH Markdown。
- 用户只要某张图：使用原生图模式；不要强加长篇计划。
- 用户明确要求纯文字、指定格式或已有执行授权：按该次要求，不重复审批。
- 设计任务只读调查业务实现，允许写方案交付；执行代码、迁移、生产写入仍以用户授权和项目规则为准。不要把“制作规划页”当作执行所有待办的授权。

## 制作完整规划

1. 先读当前项目规则和与需求有关的真实文件。核实入口、接口、数据与验证命令；区分当前事实、拟议变更、假设和未验证项。无法确认的路径或指标明确标注，不能填造。
2. 编写一份完整 Markdown 作为实施内容的唯一源。参考 [计划内容与格式](references/planning-contract.md)。它应包含目标/范围、现状依据、关键决策、涉及文件、接口/数据结构、依赖顺序、每步产出、测试/验收、风险/回滚和具体待办。
3. 按计划选择原生图，图中节点与步骤使用一致名称。阅读 [完整绘图能力](references/native-capabilities.md) 的对应类型及必要 schema；保留 JSON 图规格。架构和流程最常用，数据/状态问题按内容换图，不能一律画流水线。
4. 用本 Skill 的绝对路径运行下列命令，输出目录须为本次新目录：

```bash
node <SKILL_ROOT>/scripts/planning-page.mjs build \
  --plan <完整计划.md> --diagram <图规格.json> --type workflow \
  --out <本次交付目录>
```

可加 `--repo-root <仓库>` 以核实代码引用。脚本默认使用方案阅读版式：顶部概览、桌面侧栏目录、主规划图和顺序展开的完整章节；窄屏目录可收起，宽图与表格局部横向滚动。自动生成目录和返回链接；它不会把正文缩成摘要。普通路径和命令请用代码格式，清单和表格保持平级，避免原始 HTML；不支持的格式会明确失败，修订源稿后再生成，不得删掉关键实施内容以通过检查。

需要第二张小图可在计划源中使用内联原生指令。额外外部 JSON/CSV/图片应按完整绘图手册组织在交付目录并走原生整页流程；构建脚本仅自动复制主要图文件。

5. 脚本输出 `规划页.html`、`DSH-实施计划.md`、`candidate.visualplan.md`、图规格、内容清单和引擎收据。运行：

```bash
node <SKILL_ROOT>/scripts/planning-page.mjs check --out <本次交付目录>
node <SKILL_ROOT>/bin/visualplan.mjs browser-check <规划页.html> --json
```

`finalize explainer` 只证明自动文件检查，不证明浏览器交互。实际打开成品，检查目录跳转/返回链接、交互图展开和关闭、清单勾选/刷新，以及桌面与约 390px 窄屏的正文/长表格。记录实际尺寸，区分自动检查、浏览器检查和截图目检。运行环境缺浏览器时可交付文件，但明确列出未验证项。

6. 内容修订应修改 Markdown 和图规格，再输出一个新修订目录；保留旧稿。不要只手改 HTML 导致 DSH 内容失配。清单勾选是读者在本机的阅读进度，保存在当前页面修订下；它不自动修改 Markdown、不证明实施完成，也不代替执行验收。新修订不会继承旧任务的完成勾选。

## 独立绘图与高级能力

需要独立图、对比、代码引用、实时预览、局部修订、主题、动效或图片/SVG/WebM 导出时，按 [完整绘图能力](references/native-capabilities.md) 和其中对应参考执行。11 种入口包含 10 种原生图与整页说明。所有 CLI、渲染器、schema、离线字体、图标和图表依赖都在当前包内。

原生图首次完整稿直接执行：

```bash
node <SKILL_ROOT>/bin/visualplan.mjs finalize <类型> <图规格.json> <成品.html> --quality showcase --json
```

仓库图加 `--repo-root`，密集图可按手册选 `standard`。非零退出不是成功；修复具体问题再复核相关范围。`node <SKILL_ROOT>/bin/visualplan.mjs doctor` 可检查运行环境。

## 品牌和交付

- 产品名为“可视化规划”，页脚为“可视化规划”，不加宣传语、推广链接或求赞按钮。默认复用本包已有标识；用户指定新品牌时按其要求。
- 公共命令、页面标题和 Skill 正文使用本项目名称。许可证和非显示版权注释保留合法归属，不把第三方原作改成自己的署名。
- 当前独立版本为 `1.1.0`，未配置远程升级源。生成和导出不查询旧分发服务；本地版本未知时不能声称最新。
- 完成时给出 HTML、DSH Markdown 的可点击绝对路径，简述实际验证与重要未验项。仅生成设计时不要声称项目已实施、部署或业务验收。
