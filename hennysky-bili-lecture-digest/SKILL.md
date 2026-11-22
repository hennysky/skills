---
name: hennysky-bili-lecture-digest
description: 把 B 站视频或本地音视频转成可检索的单文件 HTML 讲义：本地 whisper 转写逐字稿、切章节、写拆解、生成页面并自检。当用户给出 B 站链接/BV 号/视频文件，说「提取文字稿、转文字、拆解视频、做成讲义页、存档课程、把课程转成网页」时使用，也适合批量处理课程视频。技能名 hennysky-bili-lecture-digest（旧名 bili-lecture-digest 的调用意图同样命中）。
license: MIT
metadata:
  version: "1.0.0"
  author: "hennysky"
  date: "2026-11-23"
---

# 视频转讲义（bili-lecture-digest）

把一段讲座视频变成四样东西：**带时间戳的逐字稿、章节地图、拆解报告、可离线搜索的 HTML 页**。

转写是工程，能全自动；拆解是判断，必须由你（模型）读逐字稿来写。**不要把「转写完成」当成「讲义完成」。**

---

## 0. 原则

1. **逐字稿必须来自真实音频**。不许根据标题猜内容、不许润色成通顺文章——保留口语，只替换确定的专有名词错字。
2. **拆解里每条结论都要能指回时间戳**。指不回去的，写成假设并标注。
3. **页面必须自包含**：不引用 CDN、不加载外部字体，断网能开。
4. **版权边界**：只做用户自己的学习与内部归档，不对外分发、不公开发布逐字稿。

---

## 1. 先决条件

```bash
command -v ffmpeg ffprobe whisper-cli   # 缺 ffmpeg: brew install ffmpeg
# 缺 whisper-cli:
brew install whisper-cpp
# 缺模型（约 1.5 GB，只需一次）:
mkdir -p ~/models/whisper && curl -L -o ~/models/whisper/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
```

模型路径可用 `WHISPER_MODEL` 覆盖。M1 Pro 参考速度：**约 1 小时音频 / 7 分钟转写**。

---

## 2. 流程

设技能目录为 `$SKILL`（本文件所在目录）。

### 第 1 步：取音频

```bash
python3 $SKILL/scripts/fetch.py "<链接或BV号或文件>" --out ~/Desktop/讲义/<名字>
```

- 支持 `https://b23.tv/...`、`BV...`、`av...`、普通链接、本地音视频。
- 产出 `meta.json` + `audio16k.wav`（16k 单声道）。
- 测试时可加 `--max-seconds 300` 只取前 5 分钟，验证链路。

### 第 2 步：转写

```bash
python3 $SKILL/scripts/transcribe.py ~/Desktop/讲义/<名字> [--clean-audio]
```

`--clean-audio` 会在转写成功后删掉 112 MB 的 wav（确认不再换模型重跑时再用）。

产出 `transcript.md`（`**[mm:ss]** 段落`）、`transcript.srt`、`segments.json`。
术语替换读两级：`glossary/zh-common.txt`（通用）+ 项目内 `glossary.txt`（本领域，优先级更高，放在项目目录）。

### 第 3 步（可选）：抽帧看画面

```bash
python3 $SKILL/scripts/frames.py ~/Desktop/讲义/<名字> --url "<视频流>" --every 20
```

屏幕共享类视频（PPT/语雀/代码）建议抽 5–15 帧，**用图片查看工具看几张**，确认章节结构与页面里的表头、公式。纯口播视频可跳过。

### 第 4 步：写 `analysis.md`（你的活，不能省）

把逐字稿读一遍（长视频分段读），按下面骨架写进项目目录的 `analysis.md`：

```markdown
## 一句话结论
（这段内容到底解决什么问题；如果只是入门课，直说"是地图不是手册"）

## 这是什么形态的内容
| 项目 | 事实 |   ← 形式、时长、数据真假、口误、信息密度

## 观看地图
| 时间 | 内容 | 值得看吗 |   ← 用逐字稿时间戳，至少 8 行

## 逐段拆解
### 3.1 …
（每段：讲了什么 → 关键定义/公式 → 讲师的例子 → 一句我的判断）

## 这套内容的能力边界（我补的）
| 缺口 | 为什么要紧 | 补法 |

## 可直接抄走的动作
1. …（能落地成步骤的，不超过 10 条）

## 名词速查
| 名词 | 一句话 |
```

**硬性要求**

- 每个 `##` 会进页面目录，**控制在 4–8 个**；不要再写一级标题。
- 关键句后面带 `（14:20）` 这类时间戳。
- 讲师说错的、数据是模拟的、公式只讲了一半——**必须写出来**，写在"能力边界"里。
- 不确定的数字标「待核」，不要四舍五入成确定值。
- 表格用 `|` 语法；公式用 `$...$` / `$$...$$`（页面内置 LaTeX 子集渲染：分数、根号、上下标、希腊字母）。

### 第 5 步：生成页面与自检

```bash
python3 $SKILL/scripts/build_page.py ~/Desktop/讲义/<名字>
python3 $SKILL/scripts/check.py       ~/Desktop/讲义/<名字>
```

`check.py` 必须全 PASS 才算完成；WARN 要能解释（例如时间覆盖 86% 是因为视频末尾是片尾）。

交付时告诉用户三件事：**页面路径、逐字稿字数、哪些是自动生成未人工校对的部分**。

---

## 3. 验收标准

| 项 | 标准 |
|---|---|
| 逐字稿覆盖 | 最后一段 ≥ 视频时长的 85% |
| 语速密度 | 200–350 字/分钟（偏离说明音频有问题或语言不同） |
| 页面 | 无外链、可离线、移动端不横向溢出、搜索可用 |
| 拆解 | 每个结论有时间戳；缺口清单非空 |
| 自检 | `check.py` 退出码 0 |

可选用浏览器打开截图确认（ego-browser），重点看：目录、表格、公式、逐字稿搜索。

---

## 4. 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `WBI 取流失败` | 接口签名/风控变了 | 会自动尝试 yt-dlp；装 `brew install yt-dlp` 兜底 |
| 字幕接口返回空 | 未登录 / 视频没有字幕 | 不用官方字幕，直接音频转写 |
| 转写全是英文乱码 | 语种判断错 | `--language zh` 显式指定 |
| 专有名词反复错 | 术语表没覆盖 | 往 `glossary.txt` 加 `错=>对`，重跑第 2 步 |
| 页面字数 0 | 先 build 后 transcribe | 重跑 `build_page.py` |
| 长视频很慢 | 正常 | 1 小时约 7 分钟；可先 `--max-seconds` 验证 |

---

## 5. 批量

```bash
for bv in BV1xxx BV2xxx; do
  python3 $SKILL/scripts/fetch.py "$bv" --out ~/Desktop/讲义/$bv &&
  python3 $SKILL/scripts/transcribe.py ~/Desktop/讲义/$bv
done
```

转写可并行，但**同时不要超过 2 个**（每个占 1.5 GB 内存 + GPU）。

---

## 6. 不要做的事

- 不要把逐字稿全文贴进对外文档或公开发布。
- 不要用"看起来合理"的内容补齐听不清的段落；标明 `[听不清]` 更诚实。
- 不要在拆解里复述整段原文；转述 + 短引用即可。
- 不要跳过 `analysis.md` 直接交付一个只有逐字稿的页面。
