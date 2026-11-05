# Skills

我日常在用的 AI Skills 集合。每个技能一个独立文件夹，可单独取用，互不依赖。

## 已收录

| 技能 | 版本 | 一句话说明 | 额外依赖 |
|---|---|---|---|
| [visual-planning](./visual-planning/) | 1.1.2 | 把方案和计划做成带原生交互图、可勾选待办的独立网页（10 种图型） | Node.js ≥ 18 |
| [report-briefing](./report-briefing/) | 1.1.2 | 把工作内容做成能交出去的汇报：先出大纲、再填要点、最后生成汇报页，按六类汇报场景匹配对应的去 AI 味规则 | 无 |
| [buddy-checkin](./buddy-checkin/) | 1.0.0 | 自动领取 Buddy加油站里所有可自动领取的积分（每日签到 + Buddy出车奖励），并汇报余额 | Python + 首次联网装 Playwright |

---

## 怎么用

每个技能文件夹里都有一份 `SKILL.md`——这是给 AI 读的说明书，也是技能的入口。

### 第一步：拿到仓库

```bash
git clone https://github.com/hennysky/skills.git
cd skills
```

没有 git 的话，直接在仓库页面点 `Code → Download ZIP` 解压，效果一样。

### 第二步：装进 WorkBuddy

技能就是文件夹，复制过去即可（以 `visual-planning` 为例）：

```bash
mkdir -p ~/.workbuddy/skills
cp -R visual-planning ~/.workbuddy/skills/
```

装完 **重启 WorkBuddy**，技能才会被识别。

### 第三步：验证能跑

`visual-planning` 装完建议跑一次自检：

```bash
cd ~/.workbuddy/skills/visual-planning && node bin/visualplan.mjs doctor
```

27 项全部 `[ok]` 即安装成功。

> ⚠️ **如果在 WorkBuddy 对话里让 AI 调用它，命令前面要加 `env -u NODE_OPTIONS`**：
> `env -u NODE_OPTIONS node bin/visualplan.mjs finalize ...`
> 原因：WorkBuddy 会给 Node 注入文件保护钩子，拦截它清理临时目录，导致回执报错（页面其实已经生成好了）。你自己在终端里跑则不需要加。

`report-briefing` 只含 Markdown 与 HTML 模板，无依赖，复制后重启即可用。

`buddy-checkin` 需要 Python 与 Playwright（缺依赖会自动在技能目录建虚拟环境装好），装完三步：`doctor` 自检 → `login` 微信扫码一次 → 建一个每天 09:30 的自动化跑 `claim.py claim`。细节见其文件夹里的 [安装说明](./buddy-checkin/安装说明.md)。

各技能的详细步骤见其文件夹内的 `安装说明.md`。

### 在对话里使用

装好后直接说人话即可，例如：

- 「用可视化规划，把这份方案做成规划页」
- 「画一张数据流转架构图」
- 「用汇报 skill 写本期双周汇报的大纲」
- 「这份述职稿帮我看下有没有 AI 味」

---

## 说明

- 各技能独立运行，互不依赖，可以只装其中一个。
- 技能内如含第三方代码，来源与许可证在对应文件夹的 `licenses/` 与 `THIRD_PARTY_NOTICES.md` 中保留原始归属。
- 仓库内**不包含任何账号凭证**。`buddy-checkin/data/session.json` 是本地扫码后生成的登录态（等同账号钥匙），由 `.gitignore` 排除，永远不会被提交——你扫码后也请勿手动提交或外传。
- 更新技能：`git pull` 后把对应文件夹重新 `cp -R` 一次，再重启客户端。
