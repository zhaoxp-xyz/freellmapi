# FreeLLMAPI 合并官方 v0.6.6 — 最终版计划（冻结版 v1.0，锚定原文）

> **冻结声明**：本文件的 6 阶段（含阶段名、输入/操作/输出/验证/完成标准）为锚定原文，
> 自 2026-08-01 用户核实通过起永久生效——任何记忆压缩、skill 精简、文档改写均不得变更此段内容，防止方向漂移。

**目标**：以官方 `tashfeenahmed/freellmapi` main（v0.6.6 `76c3e6b`）为基底，移植我们 fork 的 14 个功能提交（auxiliary 路由 / 平台补丁 / timeoutMs / OpenModel / i18n），产出"官方全部新能力 + 我们全部自主功能"合体版，部署到 40 该隐。

**执行环境**：23 平行线新建工作区 `~/freellmapi-auxiliary`（独立 clone fork，**23 红线目录 `~/freellmapi` 零接触**）；opencode serve 在 23 上跑，workspace 指向该工作区；构建产物经 rsync/scp 到 40 部署（先备份）。

**协作模式**：Hermes（平行线）= 总指挥（拆任务/写任务单/验收/维护记忆）；opencode = 编码执行（读 AGENTS.md → 实现 → 构建 → 自测）；**AGENTS.md = 项目记忆中枢**（opencode 每次会话自动加载，记录阶段进度/验证证据/踩坑，防多天改造失忆）。

**不变量（全程不得违反）**：
1. 31.23 本机 `~/freellmapi` 严禁任何改动，只读
2. 只从 fork `zhaoxp-xyz/freellmapi` 安装；克隆/构建/启动任一失败立即停下报告
3. 部署 40 前必须备份（目录 + SQLite DB + .encryption-key）
4. 每阶段完成后：汇报验证结果 → 用户确认 → 才进下一阶段

---

### 阶段 0 — 建立基线（0.5 天）
| 项 | 内容 |
|---|---|
| **输入** | 官方 main `76c3e6b`；我们 fork main `f23a553`（+计划文档 `MERGE-UPSTREAM-PLAN.md`）；opencode v1.18.9 |
| **opencode 任务** | 建 `~/freellmapi-auxiliary` 工作区 → clone fork → 建 `merge-upstream-v0.6.6` 分支（官方树为基底）→ 创建 AGENTS.md（含本冻结版计划全文）→ `npm install && npm run build` 首次验证 |
| **我的任务** | 起 opencode serve（:4096）；确认红线目录未被动；写任务单 + 权限门 |
| **输出** | 干净工作区 + AGENTS.md + 基线可构建 |
| **验证** | `npm run build` exit 0；临时起服 `/api/ping` 200 + `/v1/models` 返回官方 380 模型 |
| **完成标准** | 基线绿 → 我汇报 → 你确认 → 进阶段 1 |

### 阶段 1 — 独立模块移植（1 天，冲突≈0）
| 项 | 内容 |
|---|---|
| **输入** | 我们独有文件：auxiliary migrations×2、routes/auxiliary.ts、bynara/nara/aiand/agnes/openmodel providers |
| **opencode 任务** | 先读官方 `providers/base.ts` 确认接口 → 逐平台拷贝适配 → **每平台一个独立 commit + push**（可单独回滚） |
| **我的任务** | 维护 AGENTS.md 每平台进度；验收每个 commit 的 diff |
| **输出** | 每平台独立 commit |
| **验证** | build 通过；`/v1/models` 出现新平台模型；用 40 现有 key 实测上游 chat 200 |
| **完成标准** | 全平台 build + 实测绿 → 汇报 → 确认 → 进阶段 2 |

### 阶段 2 — 核心配置合并（0.5 天，小冲突）
| 项 | 内容 |
|---|---|
| **输入** | 官方新版 key-parser.ts / providers/index.ts / defaults.ts / app.ts |
| **opencode 任务** | 移植 PREFIX_MAP（bynara/nara/aiand 前缀）、平台注册、timeoutMs 120s、auxiliary 挂载点、migration 注册（注意 defaults.ts 3 处注册坑 + 先 build） |
| **我的任务** | 核对 migration 注册完整性；验收 diff |
| **输出** | 1 个 commit |
| **验证** | build + 单测通过；`/api/keys/providers`（官方新接口）全平台可见 |
| **完成标准** | 配置层绿 → 汇报 → 确认 → 进阶段 3 |

### 阶段 3 — router 重移植（1-2 天，最难点 ⚠️）
| 项 | 内容 |
|---|---|
| **输入** | 官方新 router.ts（fallback-loop/attempt-trace 架构）+ 我们旧 router 的 auxiliary 链逻辑 |
| **opencode 任务** | ① 通读官方新 resolveRoutingChain 定位挂载点 ② 重实现 `auto:<task_type>`（读 auxiliary_config）③ 重实现 bare name（vision/coder/general）④ 适配官方 attempt-trace 日志（顺带获得日志增强） |
| **我的任务** | 全程盯防：逐次 diff 审查 + 双人复核路由逻辑；更新 AGENTS.md 记录决策 |
| **输出** | 1 个 commit |
| **验证** | 三种请求全 200：`model=auto` / `model=auto:vision` / `model=coder`；`X-Routed-Via` 头正确；requests 表新字段（client_ip/served_model/attempts）落库正确 |
| **完成标准** | 路由三态绿 + 日志落库验证 → 汇报 → 确认 → 进阶段 4 |

### 阶段 4 — 前端移植（1 天）
| 项 | 内容 |
|---|---|
| **输入** | 我们 fork 的 AuxiliaryPage + TASK_TYPES + zh-CN i18n（439/439） |
| **opencode 任务** | 适配官方新 dashboard（60 语言、settings-dialog 重构）→ 移植 auxiliary 页面 + 5 task types UI |
| **我的任务** | 验收页面功能；zh-CN 相对官方翻译 diff 检查 |
| **输出** | 1 个 commit |
| **验证** | client build 通过；页面可操作；翻译无回退 |
| **完成标准** | 前端绿 → 汇报 → 确认 → 进阶段 5 |

### 阶段 5 — 集成 + 部署 40（1 天）
| 项 | 内容 |
|---|---|
| **输入** | `merge-upstream-v0.6.6` 全量合并结果 |
| **opencode 任务** | 全量单测 + Hermes 依赖场景冒烟（auto 路由 / auxiliary / vision / 非流式慢模型 / 流式） |
| **我的任务** | 备份 40（目录 + DB + .encryption-key）→ 部署新分支（systemd 替换，ENCRYPTION_KEY 保持）→ 验证该隐依赖（Gemma4-12B、Honcho:8000）不受影响 → 回写 skill + MemPalace |
| **输出** | 40 运行 v0.6.6 + 我们全部功能；AGENTS.md 收尾归档 |
| **验证** | ping / models / 各平台实测 / auxiliary API 全通 |
| **回退方案** | 停服 → 切回 main（f23a553）→ 起服（10 分钟内恢复） |
| **完成标准** | 40 全绿 + 该隐依赖无碍 → 汇报验收 |

---
*冻结版 v1.0，2026-08-01 用户核实通过。锚定内容，禁止压缩/变更。*
