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

- **2026-08-01 阶段 1 完成 ✅（opencode 执行 + Hermes 独立验收）**：
  - ✅ **4 个独立文件移植完成**（3 个 commit，build 通过）：
    - `a8f7100` feat(auxiliary): port auxiliary_config migrations from fork（建表 + UNIQUE 约束，78 行）
    - `2e51447` feat(auxiliary): port /api/auxiliary route from fork（107 行）
    - `62a6b94` feat(providers): port OpenModel (Anthropic Messages) provider from fork（172 行 + shared/types.ts 加 'openmodel' 平台）
  - ✅ **独立验收**：npm run build -w server 我自己跑 tsc 通过 exit 0；openmodel 与官方新 fetchWithTimeout 签名天然兼容
  - ✅ **Provider 增删架构规范落盘**（`35e05c4`）：
    - `docs/PROVIDERS.md`（4 层架构：代码层/模型层/知识层/流程层 + 15+ 平台清单 + 增删 SOP + 免费判定标准）
    - AGENTS.md §8 同步精简版（opencode 每次自动加载）
    - 宿主目录 `~/hermes-project/freellmapi/PROVIDERS-DESIGN-v1.0.md` 归档
  - 📌 **按用户指示调整**：bynara 不移植（与 nara 同后端双入口，官方已有 nara）；aiand 不移植（已弃用预付制坑，走 groq）
- **2026-08-01 阶段 2 完成 ✅（opencode 执行 + Hermes 独立验收，commit e9db2a2）**：
  - ✅ **5 个接线点全部到位**：defaults.ts 注册 2 个 auxiliary migrations（3 处：import/FILENAME/数组）；app.ts 挂载 `/api/auxiliary`（requireAuth）；providers/index.ts 注册 OpenModelMessagesProvider（degraded 注释）；key-parser.ts PREFIX_MAP 加 OPENMODEL_/OM_ + AUTH_JSON_PROVIDER_MAP 加 openmodel
  - ✅ **3 个构建错误修复**：auxiliary.ts 默认导出→命名导出 auxiliaryRouter；2 个 migrations 的 better-sqlite3 Database 类型→官方 Db 类型
  - ✅ **独立验证**：npm run build -w server tsc 通过（我自己跑）
  - ✅ **阶段 1+2 已推送远端**（6f99e83 → e9db2a2）
  - ⏳ 待办：阶段 3 router 重移植（官方新 router.ts fallback-loop/attempt-trace + 我们 auxiliary 链逻辑）
  - 📌 经验：opencode serve v1.18.9 API 是 `/api` 前缀版（`POST /api/session`、`POST /api/session/{id}/prompt`，body=`{"prompt":{"text":...},"delivery":"steer"}`）；旧 skill 里无前缀 + parts 数组格式已过时
- **2026-08-02 阶段 3 完成 ✅（commit ac3c291，opencode 执行 + Hermes 独立验收）**：
  - ✅ `feat(router): port auxiliary task-type routing (auto:<task_type> + bare name) into v0.6.6 router`
  - ✅ resolveRoutingChain 新增 3 分支：bare name（vision/coder/...）→ getChainByTaskType；`auto:<task_type>`（在 profile 查询前插入）；VALID_TASK_TYPES 常量 + isValidTaskType()
  - ✅ 与官方 attempt-trace/fallback-loop 架构兼容（ResolvedChain 形状一致），官方 global sort / profile 逻辑未动
  - ⏳ 验证补充：起服实测 `model=auto:vision` / `model=coder` 需阶段 5 冒烟时完成（build + tsc 已过）
- **2026-08-02 阶段 4 调研完成 ✅（I18N-AUDIT，文档 `~/hermes-project/freellmapi/I18N-AUDIT-v0.6.6.md`）**：
  - ✅ **数据修正（原计划 vs 实测）**：
    - ❌ "zh-CN i18n 439/439" → ✅ 官方 60 语言每文件仅 **21 个顶层命名空间 key**，60 文件完全对齐零差异；fork zh-CN 实为 16 key
    - ❌ "TASK_TYPES 5 个" → ✅ 后端 VALID_TASK_TYPES 实为 **14 个**（vision/webextract/compression/skillhub/approval/mcp/tirlegen/curator/general/coding/embedding/imagegeneration/videogen/tts）
    - ❌ "AuxiliaryPage 在 f23a553" → ✅ 实际在 **d17da9f**（feat: unify auxiliary chain management with multi-task support）
  - ✅ **官方无 auxiliary 命名空间** → 阶段 4 需新增；AuxiliaryPage 硬编码英文串 18 条 + taskMeta 14 个 task type 的 label/description 需翻译
  - ✅ **阶段 4 子任务清单**（每子任务独立 commit）：4.1 提取硬编码串→新增 auxiliary 命名空间（en.json）→ 4.2 翻译 60 语言（脚本校验 60 文件均有 auxiliary）→ 4.3 新建 AuxiliaryPage.tsx（参照 d17da9f 适配官方组件库）→ 4.4 taskMeta 对齐后端 14 个 VALID_TASK_TYPES → 4.5 App.tsx 加 /auxiliary 路由 + 导航入口 → 4.6 端到端验证（PORT=3002）
  - ⏳ **待办**：用户确认后派 opencode 执行阶段 4（当前明确指示：**暂不开工**）

## 4b. 阶段 3 任务单（router 重移植，最难点 ⚠️）

**目标**：把我们的 auxiliary 路由逻辑（task-type 链）移植进官方 v0.6.6 新版 router.ts（1514 行，fallback-loop/attempt-trace 架构）。

**已调研的差异（2026-08-01）**：
- 官方 `resolveRoutingChain`（router.ts L825）：`auto:` 后缀只认 global sort（GLOBAL_SORT_ALIASES）+ profile（getChainByProfileName）；**无 task-type 支持、无 bare name**
- 我们旧版（main 分支）：`getChainByTaskType(db, taskType)` 查 auxiliary_config JOIN models + `isValidTaskType()` bare name 分支 + `auto:<task_type>` 分支（在 profile 查询前插入）
- 官方已含：GLOBAL_SORT_ALIASES、getChainByProfileName、getChainByGlobalSort、orderChain——这些不用动

**opencode 任务（阶段 3）**：
1. 通读官方新 `resolveRoutingChain`（L825-869）定位插入点
2. 移植 `getChainByTaskType`（查 auxiliary_config，SQL 参考我们旧版，适配官方 ChainRow 类型）
3. 移植 bare name 分支（`isValidTaskType(lower)` → getChainByTaskType）
4. 在 profile 查询前插入 `auto:<task_type>` 分支（isValidTaskType(suffix)）
5. 需要时从我们旧版移植 `isValidTaskType` 函数（查 VALID_TASK_TYPES 或 auxiliary_config 存在性）
6. 适配官方 attempt-trace/fallback-loop 架构（task-type 链返回的 ResolvedChain 必须与官方形状一致）
7. 不要动官方已有的 global sort / profile 逻辑

**验证（阶段 3 完成标准）**：三种请求全 200：`model=auto` / `model=auto:vision` / `model=coder`（需要起服 + 数据库有 auxiliary_config 数据才完整验证；build + 单测为第一道关）
- `npm run build -w server` + `npm run test -w server`
- 起临时服（PORT=3002）验证 resolveRoutingChain 行为（若 DB 无 auxiliary_config 数据，可手工插入测试行或用单测覆盖）

**commit**：1 个独立 commit：`feat(router): port auxiliary task-type routing (auto:<task_type> + bare name) into v0.6.6 router`

## 5. 已实测修正事实（与官方 AGENTS.md/代码不一致，以本表为准）

| 主题 | 官方描述 | 我们实测（2026-07-31） |
|---|---|---|
| agnes 平台 | keyless: true | **实际要 key**，请求不带 key 必 401（keyless 是 bug，已修） |
| bynara | keyless: false | 确认要 key（sk-nry- 前缀），与官方一致 |
| 推理模型 timeout | 60s | **必须 120s**（agnese-2.5-pro-alpha 非流式单次 60-120s，60s 必 abort；流式不受限）→ 官方 v0.6.6 用 PROVIDER_TIMEOUT_<PLATFORM> 环境变量解决，40 部署时设环境变量 |
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

## 8. Provider 增删架构规范（2026-08-01 用户确认，强制遵守）

> **任何 provider 增/删/改必须按 `docs/PROVIDERS.md` 执行**（详细 SOP 在那）。本节是精简版，opencode 每次开工必读。

### 4 层架构
- **代码层**：`providers/index.ts` 集中 `register()`（Map<Platform, BaseProvider>）；OpenAI 兼容用 OpenAICompatProvider，特殊协议独立类。删平台**留注释**记录原因。
- **模型层**：官方 catalog 模型 → catalog-sync 自动管；**本地扩展平台模型必须 `key_id` 绑定**（或 size_label='Custom'）防 catalog-sync 误删；删模型清 auxiliary_config 孤儿。
- **知识层**：`docs/PROVIDERS.md` 平台清单表（端点/key 前缀/免费规则/模型/状态/特殊配置），**增删后必须更新**。
- **流程层**：增 7 步（调研免费→判定→代码6点→模型入库绑key→实测→更新清单→commit）/ 删 6 步（确认原因→代码留注释→key停用enabled=0→模型清理→更新清单→commit）。

### timeout 机制
- **代码不硬编码大 timeout**。官方 v0.6.6 用 `PROVIDER_TIMEOUT_<PLATFORM>` 环境变量（lib/provider-timeout.ts）。推理模型 40 部署时 systemd 设 `PROVIDER_TIMEOUT_AGNES=120000` 等。

### 免费判定
- 真免费（pricing=0）→ 接入；预付制（$0 全 404 需充值，如 aiand）→ **不接入**，找替代（aiand→groq）；已转收费 → 移除或 key 停用。
- 平台增删后 3 处必须同步：代码层 / PROVIDERS.md 清单 / auxiliary_config（如有模型引用）。

### 当前平台状态速查（详见 docs/PROVIDERS.md 全表）
- active: agnes, nara, bynara(同 nara 后端), opencode, groq, openrouter, mistral, nvidia, zhipu, github, modelscope(官方)
- degraded: openmodel（全付费，待验证）
- dropped: aiand（预付制坑，弃用走 groq）

## 9. 数据库架构落盘（2026-08-02 用户确认，必须遵守）

> **目标**：任何数据库改动以本节为准，改对了直接就能开发出正确的数据库。本节是**唯一权威**，与代码不一致时以本节为准。

### 9.1 数据库位置与版本
- **文件**：`server/data/freeapi.db`（SQLite，better-sqlite3）
- **路径解析**：`server/src/db/index.ts` `DB_PATH = path.resolve(__dirname, '../../data/freeapi.db')`，可被 `FREEAPI_DB_PATH` 环境变量覆盖
- **migrations 表**：`migrations(id, filename, applied_at)`——记录已应用迁移（当前 20 条）
- **23 部署库当前状态**：auxiliary_config 表存在（2 条 migration 已应用），14 个 key 全 healthy

### 9.2 我们新增的 auxiliary_config 表（核心）
```sql
CREATE TABLE auxiliary_config (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_type TEXT NOT NULL,        -- 'vision'/'coder'/'webextract'/... 13 个合法值（见 9.4）
  model_db_id INTEGER NOT NULL,   -- 引用 models.id，ON DELETE CASCADE
  priority INTEGER NOT NULL DEFAULT 0,   -- 链内顺序，越小越优先
  enabled INTEGER NOT NULL DEFAULT 1,
  UNIQUE (task_type, model_db_id),       -- 防重复（第二个 migration 加固）
  FOREIGN KEY (model_db_id) REFERENCES models (id) ON DELETE CASCADE
);
CREATE INDEX idx_auxiliary_task_type ON auxiliary_config (task_type);
```
- **用途**：router.ts 的 `auto:<task_type>` / bare name 路由查此表拼模型链（getChainByTaskType）
- **空表行为**：链为空 → 请求报错 "Task type 'X' has no enabled models"（功能就绪，非故障）
- **维护**：模型被删时 CASCADE 自动清孤儿；迁移/改链在 dashboard 的 Model Groups 页面操作

### 9.3 migration 注册机制（3 处，缺一不可，**先 build 再跑**）
`db:migration:up` **只跑 `server/src/db/migrate/defaults.ts` 硬编码列表**，不扫目录。新 migration 必须注册 3 处：
1. **import**：`import * as X from '../migrations/<file>.js'`（注意编译后是 .js）
2. **FILENAME 常量**：`export const X_FILENAME = '<file>.ts'`
3. **数组项**：`{ filename: X_FILENAME, module: X }` 加入 `MIGRATIONS` 数组

**现有 auxiliary 2 个 migration**（都已注册）：
| 文件 | 内容 |
|---|---|
| `20260731_120000_auxiliary_config.ts` | 建表 + task_type 索引 |
| `20260801_080000_auxiliary_config_unique.ts` | 加固 UNIQUE(task_type, model_db_id)（SQLite 不能 ALTER ADD CONSTRAINT，重建表） |

### 9.4 VALID_TASK_TYPES（13 个，2026-08-02 定稿）
```ts
['vision', 'webextract', 'compression', 'skillhub', 'approval', 'mcp',
 'curator', 'general', 'coder', 'embedding', 'imagegeneration', 'videogen', 'tts']
```
- **定义处**：`server/src/routes/auxiliary.ts`（API 返回）+ `client/src/pages/AuxiliaryPage.tsx`（前端 taskMeta）+ `server/src/services/router.ts`（路由校验，**注意 router.ts 的列表是 10 个精简版**，2026-08-02 未同步）
- **已删除**：`tirlegen`（曾存在，2026-08-02 删除，见 §10）
- **命名**：`coder` 非 `coding`（2026-07-22 前后端统一过，2026-08-02 再次确认）

### 9.5 关键表（官方已有，勿动）
`models`（模型目录）、`api_keys`（加密 key）、`fallback_config`（默认链）、`profile_models`（profile 链）、`settings`（proxy_url 等）、`requests`（**created_at 是 UTC 非 CST！**）、`sessions`（dashboard 会话，token_hash）、`users`（admin@freellmapi.dev）

## 10. Model Groups（原 Auxiliary）落盘（2026-08-02 用户确认，必须遵守）

> **目标**：后续开发前先读本节，避免理解偏差。本节记录该功能的前因后果与命名演变。

### 10.1 一句话定义
**Model Groups = 按任务类型（task_type）管理的模型链分组页**。每个 task type 是一个"组"，组内模型按 priority 排序构成路由链；router 收到 `auto:<task_type>` 或 bare name（如 `coder`）请求时按链路由。

### 10.2 命名演变（前因后果）
| 时间 | 名称 | 说明 |
|---|---|---|
| 2026-07-22 | coding→coder | 前后端 task type 统一为 coder（我们 fork 的早期工作） |
| 2026-08-01 | "Auxiliary" | 我们 fork 的 AuxiliaryPage 移植进 v0.6.6，侧边栏叫 Auxiliary，路由 `/auxiliary` |
| 2026-08-02 | "Model Groups" | 用户确认：**models/groups 原则等于 auxiliary，统一命名**。路由 `/models/groups`，60 语言本地化名称（en=Model Groups, zh-CN=模型组, ja=モデルグループ...） |

**2026-08-02 用户原话**："models/groups，原则上等于auxiliary，我们统一名字，用auxiliary的60种语言名称吧"；"用models/groups，因为页面名字叫models groups比较贴切"。

### 10.3 当前实现状态（2026-08-02 定稿）
- **路由**：`/models/groups` → AuxiliaryPage；`/auxiliary` 301 重定向到 `/models/groups`
- **导航**：侧边栏 nav item `{ to: '/models/groups', labelKey: 'nav.auxiliary' }`
- **标签**：models-tabs.tsx "Model Groups"（`models.groupsTab`）+ 新 徽章
- **任务切换**：`/models/groups?task=<task_type>`（vision 默认，无 query 时）
- **i18n key**：`auxiliary.title` / `models.groupsTab` / `nav.auxiliary` 三者同值（60 语言本地化"Model Groups"）；`auxiliary.tasks.<type>.label/description` 13 个任务
- **页面结构**：PageHeader（任务名+描述+badge）→ 任务标签条（13 个，可点切换）→ 搜索框 → Available 列表（可拖入链）→ In Chain 列表（可拖拽排序/移除）

### 10.4 已删除的 tirlegen（为什么删）
- **来源**：2026-07-01 commit `f720b40` "ui: add 5 missing task types" 加入，label "Tirlegen"，描述 "Models for tireless regeneration and retry logic"
- **删除原因（2026-08-02 用户确认）**：Hermes config.yaml 里没有 tirlegen 任务（对应的是 title_generation→model=general）；tirlegen 是"TItle ReGeneration"的误缩写，无实际任务支撑；用户原话"删掉吧，我觉得意义不大了，我原本的目的就是区分模型的智商，因为有些工作用不到比较智能的模型"
- **教训**：新增 task type 必须以 Hermes config.yaml 的 auxiliary 任务名或真实需求为依据，不造无源词汇

### 10.5 Hermes config.yaml auxiliary 任务 ↔ task type 映射（2026-08-02 实测）
Hermes config 的任务 key（snake_case）→ auxiliary task type（model 字段）：
| Hermes config 任务 | task type |
|---|---|
| vision | vision |
| web_extract | webextract |
| compression | compression |
| skills_hub | skillhub |
| approval | approval |
| mcp | mcp |
| title_generation | **general** |
| tts_audio_tags | tts |
| triage_specifier | **embedding** |
| kanban_decomposer | **coder** |
| profile_describer | **videogen** |
| curator | curator |
| monitor | **general** |

**注意**：Hermes config 任务 key 是 Hermes 内部名，auxiliary task type 是 freellmapi 路由名，两者通过 config 的 `model:` 字段映射。**Hermes config 无 imagegeneration**（ImageGen 只在 auxiliary 侧）。

## 11. 开发路径依赖（2026-08-02 用户确认，必须遵守）

> **目标**：任何开发/部署操作前先确认依赖链上的 IP 未被改动。**Hermes 脑子所在的机器是红线，不能动。**

### 11.1 模型请求链路（当前生产拓扑）
```
Hermes (23) → headroom proxy (23:8787) → freellmapi (40:3001) → auto 路由 → 上游模型
```
- **Hermes**（23）：`~/.hermes/config.yaml` → `model.provider: headroom`，`model.default: auto`
- **headroom**（23）：`systemd headroom.service`，监听 8787；**转发目标来自环境变量 `OPENAI_TARGET_API_URL`**（当前=`http://192.168.31.40:3001/v1`）
- **freellmapi**（40）：**当前 Hermes 脑子 = 该隐 40 的 freellmapi（:3001）**——**新红线，严禁任何改动**（动了=没脑子）
- **opencode**（23）：`~/.config/opencode/opencode.jsonc` → `baseURL: http://192.168.31.23:8787/v1`（走本机 headroom）

### 11.2 红线与可改（2026-08-02 重大变更，取代旧红线）
| 机器 | 目录 | 状态 |
|---|---|---|
| **31.40 该隐** | `~/freellmapi` | **🔴 新红线：Hermes 脑子，禁改禁重启**（headroom 的 OPENAI_TARGET_API_URL 指向它） |
| **31.23 平行线** | `~/freellmapi` | ✅ **可改：部署目标**（曾被降智操作破坏，2026-08-02 已用合并版恢复并部署） |
| **31.23 平行线** | `~/freellmapi-auxiliary` | ✅ 工作区（v0.6.6 合并版，分支 merge-upstream-v0.6.6） |

### 11.3 部署 SOP（改 23 的 freellmapi）
1. 在 `~/freellmapi-auxiliary` 改代码 → `npm run build` 通过
2. 同步到部署目录：`cp -a server/dist/. ~/freellmapi/server/dist/` + `cp -a client/dist/. ~/freellmapi/client/dist/`（保留 `server/data/` 和 `.env` 不动）
3. `systemctl --user restart freellmapi.service`（systemd user 服务，Restart=always）
4. 验证：`curl http://192.168.31.23:3001/api/ping` + `/v1/models` + CDP 实测页面

### 11.4 关键坑
- **改 40 = 自杀**：headroom 转发目标指向 40:3001，40 服务重启/改动会直接断 Hermes 的脑子（当前会话立即失联）
- **改 headroom 的 OPENAI_TARGET_API_URL = 换脑子**：要切换 Hermes 脑子（如切回 23）改这个环境变量 + 重启 headroom.service，但**必须先确认目标服务健康**再切，否则 Hermes 失联
- **23 的 freellmapi 服务**：systemd user 服务（`systemctl --user status/restart freellmapi`），与 40 并存，可随时切换备用
