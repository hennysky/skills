---
name: hennysky-buddy-checkin
description: 自动领取 WorkBuddy「Buddy加油站」所有可自动领取的积分（每日签到、Buddy出车奖励，并可查积分余额）。当用户说「领积分」「领一下加油站」「签到」「今天积分领了吗」「积分到账没」「重新登录加油站」时使用。首次使用需用户微信扫码登录一次，之后由技能自动创建/复用每日定时任务，全程无人值守。技能名 `hennysky-buddy-checkin`（旧名 buddy-checkin 仍可识别）。
license: MIT
metadata:
  version: "1.0.1"
  author: "hennysky"
agent_created: true
---

# Buddy加油站积分自动领取（全类型 · 可分发）

## 一句话原理

不模拟点击界面（那需要 macOS 辅助功能授权，且弹窗不一定出现），而是用**网页版登录态**在无头浏览器页面上下文里直接调平台自己的接口（Keycloak 会话 cookie 自动续期）。

## 首次安装：三步让「自动领取」跑起来

**定时靠 WorkBuddy 自动化任务，所以必须确认自动化存在，否则只会在手动喊的时候领一次。**

按顺序做，只有第 2 步需要用户在场扫码：

1. **自检**：`$PY $SKILL doctor`
   - `DOCTOR_TODO` + `SESSION missing` → 继续第 2 步
   - `DOCTOR_OK` → 跳到第 3 步
2. **登录**（唯一需要用户的操作）：`$PY $SKILL login`
   - 会弹出可见 Chrome 窗口停在微信扫码页，等 5 分钟
   - 先告诉用户：「浏览器已弹出，请用微信扫一下二维码，只需这一次」
   - 成功后打印 `LOGIN_OK`，登录态写到 `data/session.json`（权限 600，属于该用户自己，**永不外传**）
3. **建定时任务**（关键，别漏）：用 `automation_update` 创建 recurring 自动化
   - 时间：每天 09:30（`FREQ=DAILY;BYHOUR=9;BYMINUTE=30`）
   - prompt 用本文件末尾「定时任务 prompt 模板」，把路径替换成**本机真实路径**
   - 已存在同类自动化则只更新 prompt，不要重复创建

## 覆盖的积分类型（claim 一键全领）

| 类型 | 接口 | 说明 |
|---|---|---|
| 每日签到 | POST `/billing/meter/daily-checkin` | code=0 领到；code=10001 /「已签到」= 已领过，当成功 |
| Buddy出车奖励 | POST `/activity/growth/buddy/travel/claim` | 幂等；403「no unclaimed travel」= 暂无可领，正常 |
| 积分余额 | POST `/billing/meter/get-user-resource-summary` | 只查不领，输出 BALANCE |

**领不了也无需处理**：邀请好友奖励、购买返利等需真人操作的活动，脚本自动跳过。奖励包（如 100 积分礼包）到账时已直接计入余额，不存在「领取」动作。

## 四条命令

```bash
PY=~/.workbuddy/binaries/python/envs/default/bin/python3   # WorkBuddy 自带，通常都有
[ -x "$PY" ] || PY=python3                                  # 没有就用系统 python3
SKILL=~/.workbuddy/skills/hennysky-buddy-checkin/scripts/claim.py

$PY $SKILL doctor   # 自检环境/登录态（装完先跑这个）
$PY $SKILL claim    # 一键全领（日常用这个）
$PY $SKILL status   # 只查签到状态，不领取
$PY $SKILL login    # 登录/重新登录（弹浏览器扫码）
```

**环境自愈**：脚本发现当前 Python 缺 playwright，会自动在技能目录建 `.venv` 装好再重跑；没装 Chrome 就退回 Playwright 自带 chromium（必要时自动下载）。无需用户手工装依赖。

执行时如果沙箱拦截网络或弹窗，加 `dangerouslyDisableSandbox`，失败最多重试一次。

## 输出怎么读

| 输出 | 含义 | 怎么回复用户 |
|---|---|---|
| `CHECKIN_RESULT OK` | 签到刚领到（`CREDIT` 行是本次积分） | 「今日签到积分已到账」 |
| `CHECKIN_RESULT ALREADY_CLAIMED` | 今天已领过 | 「今天已领过，明天再来」 |
| `TRAVEL_RESULT OK` | 出车奖励领到（`TRAVEL_CREDIT` 行是积分数） | 「出车奖励 X 积分到账」 |
| `TRAVEL_RESULT NONE` | 暂无可领的出车奖励 | 正常，可不提 |
| `BALANCE <数字>` | 当前积分余额 | 汇报余额 |
| `OVERALL OK` | 全部正常 | 汇总即可 |
| `NEED_LOGIN` | 登录态过期 | 引导用户说「重新登录加油站」后跑 login |
| `CHECKIN_RESULT FAIL` | 接口报错 | 把 `CLAIM` 行的 msg 原样告诉用户 |

**重要坑**：`checkin-status` 返回的字段（`today_checked_in`/`active`）在活动切换期不可信。**一律以 `daily-checkin` 的返回码为准**：`code=0` 领到，`code=10001` 当成功处理。

## 定时任务 prompt 模板（分发/重建时用）

> 把 `<PY>` `<SKILL>` 换成该机器上的真实路径，再写入自动化。

```
执行命令（用 Bash 工具；如沙箱拦截网络则加 dangerouslyDisableSandbox，重试不超过一次）：
<PY> <SKILL> claim

该脚本一键领取 WorkBuddy「Buddy加油站」所有可自动领取的积分（每日签到 + Buddy出车奖励）并查余额（技能 hennysky-buddy-checkin）。根据输出报告：
1) OVERALL OK 且 CHECKIN_RESULT OK → 报告「今日积分已自动领取」（BALANCE 行是余额）；
2) CHECKIN_RESULT ALREADY_CLAIMED → 报告「今日积分已领过（每天刷新）」；TRAVEL_RESULT OK 时附「出车奖励 X 积分到账」；
3) NEED_LOGIN → 报告「登录态已失效，今日未自动领取；请对助手说『重新登录加油站』完成一次扫码后恢复自动」；
4) 其他失败 → 报告 CLAIM/TRAVEL 行的错误信息，不要盲目重试超过一次。
另外顺手执行 open -a WorkBuddy 拉起客户端。除此之外不要做任何其他操作。
```

## 登录失效怎么办

用户说「重新登录加油站」时：

1. 跑 `claim.py login`——弹出可见 Chrome 窗口停在微信扫码页，最多等 5 分钟。
2. 告诉用户：「浏览器已弹出，请用微信扫一下二维码，只需这一次」。
3. 检测到进入 `/app` 后打印 `LOGIN_OK`，登录态写回 `data/session.json`，之后定时任务自动恢复。

login 是**唯一**需要用户在场的步骤；不要在不告知用户的情况下静默弹窗。

## 安全与边界

- `data/session.json` 是账号登录态，等同钥匙：**不要打印、不要复制到工作区、不要上传、不要随技能分发**。脚本已设 600 权限。
- 只做领取/查询，不碰充值、支付、套餐变更等任何花钱的操作。
- 不要为了「自动点击」申请辅助功能权限或注入客户端进程——本方案已绕开。
- 系统级定时器（launchd/cron）在多数 macOS 上禁止第三方进程注册（实测 `launchctl bootstrap` 报 I/O error、`crontab` 报 operation not permitted），**不要尝试**，定时一律走 WorkBuddy 自动化。
