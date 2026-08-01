# FreeLLMAPI Merge-Upstream 项目工作区（AGENTS.md — 项目记忆中枢）

> **本文件是 opencode 与本项目协作者的记忆中枢**。opencode 每次会话自动加载本文件。
> 任何 agent（opencode / Hermes 平行线）开工前必须先读本文件，结束时更新"当前进度"。
> **冻结版计划（下方"锚定计划"章节）为不可变原文，禁止压缩/改写/删除。**

## 1. 项目背景

- 本项目是把我们的 fork（`zhaoxp-xyz/freellmapi`）功能合并进官方主线 `tashfeenahmed/freellmapi` v0.6.6（`76c3e6b`）的改造工程。
- 官方领先我们 149 提交（日志系统/压缩管线/缓存/模型生命周期等新功能），我们领先官方 14 提交（auxiliary 路由全家桶/平台补丁/timeoutMs/OpenModel/i18n）。
- 最终产物部署到 31.40 该隐（systemd freellmapi.service :3001，该隐依赖此服务）。

## 2. 工作区与红线（最高优先级）

- **本工作区**：`~/freellmapi-auxiliary`（23 平行机）。当前分支 `merge-upstream-v0.6.6`（基于官方树 76c3e6b）。
- **红线 1**：31.23 本机 `~/freellmapi`（平行线 + opencode 的模型大脑，headroom→freellmapi）**严禁任何改动，只读**。
- **红线 2**：只从 fork `zhaoxp-xyz/freellmapi` 安装；克隆/构建/启动任一失败立即停下报告，绝不绕路。
- **红线 3**：部署 40 前必须备份（目录 + SQLite DB + .encryption-key）。
- **红线 4**：每阶段完成后汇报验证结果 → 用户确认 → 才进下一阶段。
- remote：`origin` = zhaoxp-xyz/freellmapi（fork，主推送目标）；`upstream` = tashfeenahmed/freellmapi（官方，只拉不推）。

## 3. 锚定计划（冻结版 v1.0，2026-08-01 用户核实通过，禁止压缩/变更）

**目标**：以官方 main（v0.6.6 `76c3e6b`）为基底，移植我们 fork 的 14 个功能提交（auxiliary 路由 / 平台补丁 / timeoutMs / OpenModel / i18n），产出"官方全部新能力 + 我们全部自主功能"合体版，部署到 40 该隐。

**协作模式**：Hermes（平行线）= 总指挥（拆任务/写任务单/验收/维护记忆）；opencode = 编码执行（读本文件 → 实现 → 构建 → 自测）；本 AGENTS.md = 项目记忆中枢。

### 阶段 0 — 建立基线（0.5 天）
- **输入**：官方 main `76c3e6b`；我们 fork main `f23a553`（+计划文档）；opencode v1.18.9
- **opencode 任务**：建工作区（已完成）→ clone fork（已完成）→ 建 `merge-upstream-v0.6.6` 分支官方树基底（已完成）→ 创建 AGENTS.md（本文件）→ `npm install && npm run build` 首次验证
- **我的任务**（Hermes）：起 opencode serve（:4096）；确认红线目录未被动；写任务单 + 权限门
- **输出**：干净工作区 + AGENTS.md + 基线可构建
- **验证**：`npm run build` exit 0；临时起服 `/api/ping` 200 + `/v1/models` 返回官方 380 模型
- **完成标准**：基线绿 → 汇报 → 用户确认 → 进阶段 1

### 阶段 1 — 独立模块移植（1 天，冲突≈0）
- **输入**：我们独有文件：auxiliary migrations×2、routes/auxiliary.ts、bynara/nara/aiand/agnes/openmodel providers
- **opencode 任务**：先读官方 `providers/base.ts` 确认接口 → 逐平台拷贝适配 → **每平台一个独立 commit + push**（可单独回滚）
- **验证**：build 通过；`/v1/models` 出现新平台模型；用 40 现有 key 实测上游 chat 200

### 阶段 2 — 核心配置合并（0.5 天，小冲突）
- **输入**：官方新版 key-parser.ts / providers/index.ts / defaults.ts / app.ts
- **opencode 任务**：移植 PREFIX_MAP（bynara/nara/aiand 前缀）、平台注册、timeoutMs 120s、auxiliary 挂载点、migration 注册（注意 defaults.ts 3 处注册坑 + 先 build）
- **验证**：build + 单测通过；`/api/keys/providers`（官方新接口）全平台可见

### 阶段 3 — router 重移植（1-2 天，最难点 ⚠️）
- **输入**：官方新 router.ts（fallback-loop/attempt-trace 架构）+ 我们旧 router 的 auxiliary 链逻辑
- **opencode 任务**：① 通读官方新 resolveRoutingChain 定位挂载点 ② 重实现 `auto:<task_type>`（读 auxiliary_config）③ 重实现 bare name（vision/coder/general）④ 适配官方 attempt-trace 日志（顺带获得日志增强）
- **验证**：三种请求全 200：`model=auto` / `model=auto:vision` / `model=coder`；`X-Routed-Via` 头正确；requests 表新字段（client_ip/served_model/attempts）落库正确

### 阶段 4 — 前端移植（1 天）
- **输入**：我们 fork 的 AuxiliaryPage + TASK_TYPES + zh-CN i18n（439/439）
- **opencode 任务**：适配官方新 dashboard（60 语言、settings-dialog 重构）→ 移植 auxiliary 页面 + 5 task types UI
- **验证**：client build 通过；页面可操作；翻译无回退

### 阶段 5 — 集成 + 部署 40（1 天）
- **输入**：`merge-upstream-v0.6.6` 全量合并结果
- **opencode 任务**：全量单测 + Hermes 依赖场景冒烟（auto 路由 / auxiliary / vision / 非流式慢模型 / 流式）
- **我的任务**（Hermes）：备份 40（目录 + DB + .encryption-key）→ 部署新分支（systemd 替换，ENCRYPTION_KEY 保持）→ 验证该隐依赖（Gemma4-12B、Honcho:8000）不受影响 → 回写 skill + MemPalace
- **验证**：ping / models / 各平台实测 / auxiliary API 全通
- **回退方案**：停服 → 切回 main（f23a553）→ 起服（10 分钟内恢复）

## 4. 当前进度（每次会话结束时更新）

- **2026-08-01 阶段 0 完成 ✅（Hermes 独立验收，opencode 执行）**：
  - ✅ 冻结版计划落盘：40 仓库 `MERGE-UPSTREAM-PLAN.md`（commit 6376240）+ 本机 `~/hermes-project/freellmapi/FROZEN-PLAN-v1.0.md` + skill 锚定
  - ✅ 工作区 `~/freellmapi-auxiliary`，分支 `merge-upstream-v0.6.6` = 官方 76c3e6b
  - ✅ AGENTS.md（本文件）创建（commit 8a36c5d）
  - ✅ opencode serve :4096 运行中（v1.18.9，正确端点带 /api 前缀）
  - ✅ npm install 成功（768 包，18s）+ npm run build 成功（server/cli/client 三包 dist 齐全）
  - ✅ 临时起服（PORT=3002，避开红线 3001）：/api/ping 200；/v1/models 用 unified key 返回 **82 模型**（官方 catalog-sync v2026.07.31 默认子集——"380 模型"是官网全量宣传数，本地基线就是 82，完整扩展需阶段 1 绑定平台 key）
  - ✅ 红线目录 ~/freellmapi 全程未动
  - 📌 阶段 0 待用户确认 → 进阶段 1
  - 📌 经验：opencode serve v1.18.9 API 是 `/api` 前缀版（`POST /api/session`、`POST /api/session/{id}/prompt`，body=`{"prompt":{"text":...},"delivery":"steer"}`）；旧 skill 里无前缀 + parts 数组格式已过时

## 5. 已实测修正事实（与官方 AGENTS.md/代码不一致，以本表为准）

| 主题 | 官方描述 | 我们实测（2026-07-31） |
|---|---|---|
| agnes 平台 | keyless: true | **实际要 key**，请求不带 key 必 401（keyless 是 bug，已修） |
| bynara | keyless: false | 确认要 key（sk-nry- 前缀），与官方一致 |
| 推理模型 timeout | 60s | **必须 120s**（agnese-2.5-pro-alpha 非流式单次 60-120s，60s 必 abort；流式不受限） |
| catalog-sync 删模型 | 同步删 | **本地扩展平台模型必须 key_id 绑定**（否则被删），size_label='Custom' 也可防 |
| migration 注册 | db:migration:up | **只跑 defaults.ts 硬编码列表**（不扫目录），新 migration 须注册 3 处（import 编译后 .js / filename 常量 / 数组项）且先 build |
| aiand | 文档标 Free | **预付制坑**：$0 余额全 404，已弃用走 groq；40 上 key enabled=0 保留 |

## 6. 验证命令速查

```bash
# 构建（本工作区）
npm install && npm run build

# 起服（临时，验证用；注意 23 的 3001 被红线服务占用，临时起服要换端口或停红线服务——优先用 --port 或 PORT 环境变量）
PORT=3002 npm run start -w server   # 或 node server/dist/index.js

# 健康/模型
curl http://127.0.0.1:3002/api/ping
curl http://127.0.0.1:3002/v1/models | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))"

# 单测（server）
npm run test -w server
```

## 7. opencode 工作规范

- 每阶段一个任务单（Hermes 下发），完成标准见上方锚定计划各阶段"验证"。
- 阶段 1 起：每个独立功能 = 独立 commit（如 `feat(provider): bynara`），commit message 遵循 conventional commits。
- 改动前先 `git log --oneline -5` 看当前状态；改动后 `git diff --stat` 自查；构建失败先看错误再修，不盲试。
- 涉及红线目录（~/freellmapi）的任何路径：**禁止读写**。所有工作在 ~/freellmapi-auxiliary 内。
- 拿不准的接口/行为：先 grep 官方代码确认，不臆测；复杂决策记录到本文件第 4 节。
