# Skills

我日常在用的 AI Skills 集合。每个技能一个独立文件夹，可单独取用，互不依赖。

技能名统一加 `hennysky-` 前缀，避免和别人的同名技能撞车。

## 已收录

| 技能 | 版本 | 一句话说明 | 额外依赖 |
|---|---|---|---|
| [hennysky-visual-planning](./hennysky-visual-planning/) | 1.1.3 | 把方案和计划做成带原生交互图、可勾选待办的独立网页（10 种图型） | Node.js ≥ 18 |
| [hennysky-report-briefing](./hennysky-report-briefing/) | 1.1.3 | 把工作内容做成能交出去的汇报：先出大纲、再填要点、最后生成汇报页，按六类汇报场景匹配对应的去 AI 味规则 | 无 |
| [hennysky-buddy-checkin](./hennysky-buddy-checkin/) | 1.0.1 | 自动领取 Buddy加油站里所有可自动领取的积分（每日签到 + Buddy出车奖励），并汇报余额 | Python + 首次联网装 Playwright |
| [hennysky-bili-lecture-digest](./hennysky-bili-lecture-digest/) | 1.0.0 | 把 B 站视频转成可离线搜索的单文件 HTML 讲义：本地转写逐字稿、写拆解、生成页面并自检 | ffmpeg、whisper.cpp、1.5 GB 模型 |

> 早期版本叫 `visual-planning` / `report-briefing` / `buddy-checkin`。装过旧版的，把旧文件夹删掉、按下面步骤重装一次即可，旧调用名仍然能命中。

---

## 如何使用

**请把下面这段提示词复制粘贴给你的 Agent**，它会自己把技能装好；装完你再发视频链接就行。

```text
请帮我安装一个技能：hennysky-bili-lecture-digest，用来把 B 站视频转成可搜索的 HTML 讲义。

来源：GitHub 仓库 https://github.com/hennysky/skills ，技能在 hennysky-bili-lecture-digest 目录里。

请按顺序做：
1. 下载仓库：git clone --depth 1 https://github.com/hennysky/skills.git
2. 把 hennysky-bili-lecture-digest 整个文件夹复制到你自己的技能目录（例如 ~/.claude/skills、~/.agents/skills、~/.workbuddy/skills，按你实际使用的客户端选）。
3. 进入该文件夹，运行：python3 scripts/doctor.py
   它会列出缺什么：
   - 缺 ffmpeg 或 whisper-cli：macOS 执行 brew install ffmpeg whisper-cpp
   - 缺模型：按脚本提示下载到 ~/models/whisper/ggml-large-v3-turbo.bin（约 1.5 GB，只需一次）
4. 装完再跑一次 doctor.py，确认全部 PASS。
5. 读一遍 SKILL.md，了解使用流程。

完成后告诉我「已装好」，并告诉我：以后直接把 B 站链接发给你就行。
如果中途需要我手动操作（没有 Homebrew、没有权限、或者是 Windows 系统），停下来把具体命令发给我。
```

> 它只往你的技能目录写一个文件夹；依赖是 ffmpeg 与 whisper.cpp，模型 1.5 GB；转写全程在本机跑，视频不上传。

---

## 手动安装（可选）

不想复制提示词，就按下面步骤手动来。

每个技能文件夹里都有一份 `SKILL.md`——这是给 AI 读的说明书，也是技能的入口。

### 第一步：拿到仓库

```bash
git clone https://github.com/hennysky/skills.git
cd skills
```

没有 git 的话，直接在仓库页面点 `Code → Download ZIP` 解压，效果一样。

### 第二步：装进 WorkBuddy

技能就是文件夹，复制过去即可（以 `hennysky-visual-planning` 为例）：

```bash
mkdir -p ~/.workbuddy/skills
cp -R hennysky-visual-planning ~/.workbuddy/skills/
```

四个一起装：

```bash
cp -R hennysky-visual-planning hennysky-report-briefing hennysky-buddy-checkin hennysky-bili-lecture-digest ~/.workbuddy/skills/
```

**文件夹名不要改。** 技能靠文件夹名识别，改名（比如变成 `hennysky-visual-planning 2`）会导致装不上。

装完 **重启 WorkBuddy**，技能才会被识别。

### 第三步：验证能跑

`hennysky-visual-planning` 装完建议跑一次自检：

```bash
cd ~/.workbuddy/skills/hennysky-visual-planning && node bin/visualplan.mjs doctor
```

27 项全部 `[ok]`、最后显示 `VisualPlan is ready.` 即安装成功。

> ⚠️ **如果在 WorkBuddy 对话里让 AI 调用它，命令前面要加 `env -u NODE_OPTIONS`**：
> `env -u NODE_OPTIONS node bin/visualplan.mjs finalize ...`
> 原因：WorkBuddy 会给 Node 注入文件保护钩子，拦截它清理临时目录，导致回执报错（页面其实已经生成好了）。你自己在终端里跑则不需要加。

`hennysky-report-briefing` 只含 Markdown 与 HTML 模板，无依赖，复制后重启即可用。

`hennysky-buddy-checkin` 需要 Python 与 Playwright（缺依赖会自动在技能目录建虚拟环境装好），装完三步：`doctor` 自检 → `login` 微信扫码一次 → 建一个每天 09:30 的自动化跑 `claim.py claim`。细节见其文件夹里的 [安装说明](./hennysky-buddy-checkin/安装说明.md)。

各技能的详细步骤见其文件夹内的 `安装说明.md`。

### 在对话里使用

装好后直接说人话即可，例如：

- 「用可视化规划，把这份方案做成规划页」
- 「画一张数据流转架构图」
- 「用汇报 skill 写本期双周汇报的大纲」
- 「这份述职稿帮我看下有没有 AI 味」
- 「把这个 B 站视频做成讲义」

也可以叫英文名 `$hennysky-visual-planning`（旧名 `$visual-planning` 同样有效）。

---

## 说明

- 各技能独立运行，互不依赖，可以只装其中一个。
- 技能内如含第三方代码，来源与许可证在对应文件夹的 `licenses/` 与 `THIRD_PARTY_NOTICES.md` 中保留原始归属。
- 仓库内**不包含任何账号凭证**。`hennysky-buddy-checkin/data/session.json` 是本地扫码后生成的登录态（等同账号钥匙），由 `.gitignore` 排除，永远不会被提交——你扫码后也请勿手动提交或外传。
- 更新技能：`git pull` 后把对应文件夹重新 `cp -R` 一次，再重启客户端。
