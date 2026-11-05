# 可视化规划

独立的可视化与方案交付项目，版本 **1.1.0**。包含完整绘图引擎、Skill、离线 HTML 阅读器、计划构建与交接工具；运行时不依赖另一个 Skill 的目录。

以“可视化规划”展示，不加宣传语。支持 10 种原生图、整页说明、图表、可勾选待办、深浅主题、动效、图片/SVG/WebM 导出、校验、局部修订和实时预览。不同图型和导出格式的验证范围见 `docs/VERIFICATION.md`。

规划页默认使用专门的方案阅读版式：清晰的标题与概览、桌面侧栏目录、原生规划图、连续正文和本机待办进度。窄屏目录可折叠，宽表格与图形在局部滚动；主题和四种样式仍可切换。

## 使用

运行环境为 Node.js 18+；打包和安装脚本另需 Python 3。随包已带运行时 schema 验证器、字体、图标与静态图表渲染代码。只有重新生成验证器等开发工作需要 `npm ci`。

```bash
node bin/visualplan.mjs doctor
node bin/visualplan.mjs --help
node scripts/planning-page.mjs build --plan 计划.md --diagram 流程图.json --type workflow --out output/本次规划
node scripts/planning-page.mjs check --out output/本次规划
npm test
npm run smoke
npm run package:skill
```

Skill 安装包由项目自身构建。解压后放在个人技能目录的 `hennysky-visual-planning/`，调用 `$hennysky-visual-planning`。完整用法与交付约束见 `SKILL.md`。

## 维护

- `bin/`、`renderers/`、`schemas/`、`explainer/`：独立引擎。
- `scripts/planning-page.mjs`：同源生成网页和 DSH 文档，校验内容指纹。
- `references/`：原生图能力与规划契约。
- `tests/`、`docs/`：回归和本次验证边界。
- `licenses/`、`LICENSE`、`THIRD_PARTY_NOTICES.md`：第三方来源、原文版权和许可。

本项目在开源代码基础上独立维护，没有将第三方代码冒充原创。原版权文字只保留于许可/来源记录和输出文件的非显示版权注释。未配置远程升级仓库，生成不访问外部更新服务。新版本需在本项目审查和验证后另行分发。
