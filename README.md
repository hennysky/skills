# Skills

我日常在用的 AI Skills 集合。每个技能一个独立文件夹，可单独取用。

## 已收录

| 技能 | 版本 | 一句话说明 |
|---|---|---|
| [visual-planning](./visual-planning/) | 1.1.1 | 把方案和计划做成带原生交互图、可勾选待办的独立网页（10 种图型） |

---

## 怎么用

每个技能文件夹里都有一份 `SKILL.md`——这是给 AI 读的说明书，也是技能的入口。

### 安装到 WorkBuddy / Codex

以 `visual-planning` 为例：

```bash
mkdir -p ~/.workbuddy/skills
cp -R visual-planning ~/.workbuddy/skills/
cd ~/.workbuddy/skills/visual-planning && node bin/visualplan.mjs doctor
```

自检全部 `[ok]` 即安装成功，具体步骤见各技能内的 `安装说明.md`。

### 在对话里使用

直接说人话即可，例如：

- 「用可视化规划，把这份方案做成规划页」
- 「画一张数据流转架构图」

---

## 说明

- 各技能独立运行，互不依赖。
- 技能内如含第三方代码，来源与许可证在对应文件夹的 `licenses/` 与 `THIRD_PARTY_NOTICES.md` 中保留原始归属。
- 本仓库为个人工作工具集，非对外发布版本。
