# Skills

我日常在用的 AI Skills 集合。每个技能一个独立文件夹，可单独取用，互不依赖。

技能名统一加 `hennysky-` 前缀，避免和别人的同名技能撞车。

## 已收录

| 技能 | 版本 | 一句话说明 | 额外依赖 |
|---|---|---|---|
| [hennysky-visual-planning](./hennysky-visual-planning/) | 1.1.3 | 把方案和计划做成带原生交互图、可勾选待办的独立网页（10 种图型） | Node.js ≥ 18 |
| [hennysky-report-briefing](./hennysky-report-briefing/) | 1.1.3 | 把工作内容做成能交出去的汇报：先出大纲、再填要点、最后生成汇报页，按六类汇报场景匹配对应的去 AI 味规则 | 无 |
| [hennysky-buddy-checkin](./hennysky-buddy-checkin/) | 1.0.1 | 自动领取 Buddy加油站里所有可自动领取的积分（每日签到 + Buddy出车奖励），并汇报余额 | Python + 首次联网装 Playwright |
| [hennysky-bili-lecture-digest](./hennysky-bili-lecture-digest/) | 1.1.0 | 把 B 站视频转成可离线搜索的单文件 HTML 讲义：本地转写逐字稿、写拆解、生成页面并自检 | ffmpeg、whisper.cpp、1.5 GB 模型 |

> 早期版本叫 `visual-planning` / `report-briefing` / `buddy-checkin`。装过旧版的，把旧文件夹删掉、按下面步骤重装一次即可，旧调用名仍然能命中。

---

## 如何使用

每个技能一段提示词。**只复制你要的那一段**发给 Agent，它就会只装这一个技能，其它不会动。

装完再按对应方式使用；遇到装不上，Agent 会停下来把命令给你。

### 视频转讲义 · `hennysky-bili-lecture-digest`

```text
请帮我安装技能 hennysky-bili-lecture-digest（把 B 站视频转成可搜索的 HTML 讲义）。

来源：https://github.com/hennysky/skills ，只需要仓库里的 hennysky-bili-lecture-digest 这一个文件夹。

1. 下载仓库：git clone --depth 1 https://github.com/hennysky/skills.git
2. 只把 hennysky-bili-lecture-digest 复制到你的技能目录（例如 ~/.agents/skills、~/.workbuddy/skills、~/.claude/skills），其它技能不要装。
3. 进入该文件夹，运行 python3 scripts/doctor.py，按它列出的缺项安装：
   - ffmpeg / whisper-cli：macOS 执行 brew install ffmpeg whisper-cpp
   - 模型：下载到 ~/models/whisper/ggml-large-v3-turbo.bin（约 1.5 GB，只需一次）
4. 再跑一次 doctor.py，全部 PASS 即成功。
5. 读 SKILL.md，之后我直接把 B 站链接发给你。

完成后告诉我「已装好」。需要我手动操作时（没 Homebrew / 没权限 / Windows），停下来把命令发我。
```

### 可视化规划 · `hennysky-visual-planning`

```text
请帮我安装技能 hennysky-visual-planning（把方案做成带交互图的独立网页）。

来源：https://github.com/hennysky/skills ，只需要仓库里的 hennysky-visual-planning 这一个文件夹。

1. 下载仓库：git clone --depth 1 https://github.com/hennysky/skills.git
2. 只把 hennysky-visual-planning 复制到你的技能目录（例如 ~/.agents/skills、~/.workbuddy/skills、~/.claude/skills），其它技能不要装。
3. 确认本机有 Node.js 18 以上（node -v），没有就先装。
4. 进入该文件夹，运行 node bin/visualplan.mjs doctor，27 项全 [ok] 且出现 VisualPlan is ready. 即成功。
5. 读 SKILL.md，之后我让你画图时直接用。

完成后告诉我「已装好」。如果我是 WorkBuddy 环境，提醒我调用时要加 env -u NODE_OPTIONS。
```

### 汇报 · `hennysky-report-briefing`

```text
请帮我安装技能 hennysky-report-briefing（把工作内容做成能交出去的汇报）。

来源：https://github.com/hennysky/skills ，只需要仓库里的 hennysky-report-briefing 这一个文件夹。

1. 下载仓库：git clone --depth 1 https://github.com/hennysky/skills.git
2. 只把 hennysky-report-briefing 复制到你的技能目录（例如 ~/.agents/skills、~/.workbuddy/skills、~/.claude/skills），其它技能不要装。
3. 这个技能没有额外依赖，不需要装任何东西。
4. 读 SKILL.md；然后用一句「帮我做一份本期双周汇报的大纲」验证它能跑通，能先出大纲再填内容就对了。
5. 之后我让你写汇报时直接用。

完成后告诉我「已装好」。
```

### Buddy 积分 · `hennysky-buddy-checkin`

```text
请帮我安装技能 hennysky-buddy-checkin（自动领取 Buddy 加油站积分）。

来源：https://github.com/hennysky/skills ，只需要仓库里的 hennysky-buddy-checkin 这一个文件夹。

1. 下载仓库：git clone --depth 1 https://github.com/hennysky/skills.git
2. 只把 hennysky-buddy-checkin 复制到你的技能目录（例如 ~/.agents/skills、~/.workbuddy/skills、~/.claude/skills），其它技能不要装。
3. 进入该文件夹，运行 python3 scripts/claim.py doctor 自检（缺 Playwright 不用管，第一次运行会自动装）。
4. 运行 python3 scripts/claim.py login，弹出的页面需要我本人微信扫码，扫完告诉我。
5. 再运行 python3 scripts/claim.py claim，看到 OVERALL OK 即成功；然后读 SKILL.md，帮我建一个每天 9:30 的自动任务。

完成后告诉我「已装好」。登录态只存在本机，不要提交到任何仓库。
```

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
