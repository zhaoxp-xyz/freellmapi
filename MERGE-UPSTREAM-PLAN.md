# FreeLLMAPI 合并官方 v0.6.6 改造计划（MERGE-UPSTREAM-PLAN）

> 状态：**已批准方案，暂缓执行**（2026-08-01 用户指令"暂不开始改造"，先做分支清理落盘）
> 执行前必须重新向用户确认启动。
> 权威维护方：平行线（31.23）。执行环境：该隐（31.40）。

## 一、背景与目标

- 我们 fork（`zhaoxp-xyz/freellmapi`）分叉自官方 `tashfeenahmed/freellmapi` @ `c2f1dee`。
- 官方已演进至 **v0.6.6（`76c3e6b`）**，领先我们 **149 提交**；我们领先官方 **14 提交**（Hermes 集成改造）。
- 官方新功能令用户向往（日志系统大幅完善：log-redaction / attempt-trace / request 增强；另有压缩管线、缓存、模型生命周期、/livez /readyz 等）。
- **目标**：以官方 main（v0.6.6）为基底，把我们的 14 个功能提交逐个移植上去，得到"官方全部新能力 + 我们全部自主功能"的合体版本，部署到 40 该隐。

## 二、仓库现状（2026-08-01 清理后）

- **main** @ `f23a553` = 唯一主分支（fork 基底 `9772ad6` + 我们 14 个功能提交）。
- 已删除：`deploy-20260731`、`feat/auxiliary-routing`、`feat/auxiliary-routing-v2`（本地+远端）；`feat/modelscope-provider` 远端本就不存在。
- 保留：`stash@{0}`（pre-update-20260731 手工改动存档，勿删）。
- 备份残留 ×4 已清理（client.backup_20260727_124916/ 等）。
- 工作区干净；远端仅 `main` 一条线。

## 三、差异分析结论（2026-08-01 实测）

### 我们 fork 独有（官方没有，需移植）
| # | 功能 | 涉及文件 |
|---|---|---|
| 1 | auxiliary 任务路由：`auto:<task_type>` + bare name（vision/coder/general） | routes/auxiliary.ts、services/router.ts、migrations×2、client AuxiliaryPage |
| 2 | 平台补丁：bynara/nara/aiand providers + agnes extraHeaders | providers/、key-parser.ts、keys.ts、types.ts、KeysPage |
| 3 | timeoutMs 120s（推理模型非流式防 abort） | providers/index.ts |
| 4 | OpenModel provider（Anthropic Messages 协议） | providers/openmodel-messages.ts |
| 5 | i18n 中文翻译（439/439）+ 5 task types UI | client/ |

### 合并冲突高危区（双方都改过，共 7 个文件）
```
server/src/app.ts
server/src/db/migrate/defaults.ts
server/src/lib/key-parser.ts
server/src/providers/index.ts
server/src/routes/keys.ts
server/src/routes/proxy.ts          ← 官方 +1052 行重写
server/src/services/router.ts       ← 官方 +759 行重写，冲突最重
```

### 官方新增而我们没有的关键模块
- 日志系统：`lib/log-redaction.ts`（console 凭据脱敏 17+ 前缀）、`lib/attempt-trace.ts` + `request_attempts` 表（fallback 阶梯全记录）、request-log 增强（client_ip/user_agent/agent、served_model、requested_model）、`lib/client-context.ts`、`lib/client-classifier.ts`、`services/health.ts` +346、migrations×6
- 压缩管线 `services/compression/`（20 文件：dedup/aging/relevance/toolfilter/jsoncompact + fidelity-gate）
- 请求缓存 `services/cache.ts` + `routes/cache.ts`
- 模型生命周期：model-discovery / model-retirement / model-state / custom-endpoint / custom-model-seed / model-groups
- 路由大改：router.ts +759、proxy.ts +1052、responses.ts +834、fallback-loop.ts（统一四 provider fallback）
- 其他：routes/ollama(+607)/gemini/mcp/status/url-tokens、cooldown-probe、/livez /readyz、socks5h 代理、60 语言 dashboard、安全加固（#498）、ModelScope provider（#581 已合入官方）

## 四、合并策略（重要决策）

**不用 git merge**——官方 proxy/router 重写上千行，直接 merge 产出灾难性冲突。
**采用：官方 main 为基底重建 → 我们的功能逐个移植（cherry-pick 语义 + 手工适配）。**

执行环境：fork 新建分支 `merge-upstream-v0.6.6`（官方树为基底）。23 本机零接触；40 只在阶段 5 动（先备份）。

## 五、阶段计划（每阶段独立可验证、可组合、可单独回滚）

### 阶段 0 — 建立基线（0.5 天）
- 输入：官方 main `76c3e6b` + 我们 fork main `f23a553`
- 操作：
  1. fork 建分支 `merge-upstream-v0.6.6`，以官方树为基底
  2. 全量 diff 清点我们独有文件（providers/、client/、i18n）
  3. 备份 40 当前部署（目录 + SQLite DB + .encryption-key）
- 输出：干净工作区 + 基线可构建
- 验证：`npm run build` exit 0；临时起服 → `/api/ping` 200 + `/v1/models` 返回官方 380 模型

### 阶段 1 — 独立模块移植（1 天，冲突≈0）
- 输入：我们独有文件清单（auxiliary migrations×2、routes/auxiliary.ts、bynara/nara/aiand/agnes/openmodel providers）
- 操作：逐个拷贝 → 适配新版 `BaseProvider` 接口（先读官方 base.ts，149 提交可能改了签名）→ 每平台一个 commit + push
- 输出：每平台独立 commit，可单独回滚
- 验证：build 通过；`/v1/models` 出现新平台模型；用 40 现有 key 实测上游 chat 200

### 阶段 2 — 核心配置合并（0.5 天，小冲突）
- 输入：官方新版 key-parser.ts / providers/index.ts / defaults.ts / app.ts
- 操作：移植 PREFIX_MAP（bynara/nara/aiand 前缀）、平台注册、timeoutMs 120s、auxiliary 挂载点、migration 注册
- 输出：1 个 commit
- 验证：build + 单测通过；`/api/keys/providers`（官方新接口）全平台可见

### 阶段 3 — router 重移植（1-2 天，最难点 ⚠️）
- 输入：官方新 router.ts（fallback-loop/attempt-trace 架构）+ 我们旧 router 的 auxiliary 链逻辑
- 操作：
  1. 通读官方新 resolveRoutingChain，定位挂载点
  2. 重实现 `auto:<task_type>`（读 auxiliary_config）
  3. 重实现 bare name（vision/coder/general）
  4. 适配官方新 attempt-trace 日志（顺带获得日志增强）
- 输出：1 个 commit
- 验证：三种请求全 200：`model=auto`、`model=auto:vision`、`model=coder`；`X-Routed-Via` 头正确；requests 表新字段（client_ip/served_model/attempts）落库正确

### 阶段 4 — 前端移植（1 天）
- 输入：我们 fork 的 AuxiliaryPage + TASK_TYPES + zh-CN i18n（439/439）
- 操作：适配官方新 dashboard（60 语言、settings-dialog 重构）→ 移植 auxiliary 页面
- 输出：1 个 commit
- 验证：client build 通过；页面可操作；zh-CN 相对官方翻译 diff 检查无回退

### 阶段 5 — 集成 + 部署 40（1 天）
- 输入：`merge-upstream-v0.6.6` 全量合并结果
- 操作：
  1. 全量单测 + Hermes 依赖场景冒烟（auto 路由 / auxiliary / vision / 非流式慢模型 / 流式）
  2. 备份 40（目录 + DB + .encryption-key）
  3. 部署新分支（systemd 替换，ENCRYPTION_KEY 保持）
  4. 回写 skill + MemPalace
- 输出：40 运行 v0.6.6 + 我们全部功能
- 验证：ping / models / 各平台实测 / auxiliary API 全通；该隐依赖（Gemma4-12B、Honcho:8000）不受影响
- **回退方案**：停服 → 切回 main（f23a553）→ 起服（10 分钟内可恢复）

## 六、关键风险与对策

1. **40 DB 兼容**：官方新 migration 往 requests 表加列（nullable，安全）；auxiliary_config 表已存在 → migration 有执行记录会自动跳过，需实测确认
2. **catalog-sync 删模型**：新版本逻辑可能更激进 → 移植后立即给本地扩展平台模型绑 key_id（防删铁律）
3. **provider 基类接口变化**：官方 149 提交可能改了 BaseProvider 签名 → 阶段 1 先读官方 base.ts 再适配
4. **该隐失联风险**：阶段 5 备份+回退方案先行，选低峰时段部署
5. **migration 注册坑**（已实测）：`npm run db:migration:up` 只跑 defaults.ts 硬编码列表；新 migration 须注册 3 处（import 编译后 .js / filename 常量 / 数组项）且先 build 再跑

## 七、铁律提醒（执行时不可违反）

- **31.23 本机 `~/freellmapi`：严禁任何改动**（平行线 + opencode 依赖），只读。改 bug 只部署 40。
- 只从 fork `zhaoxp-xyz/freellmapi` 安装；克隆/构建/启动任一失败立即停下报告用户。
- 部署 40 前必须备份（该隐依赖此服务，部署失败=该隐失联）。
- 先汇报拿授权 → 全量 grep 现状 → 脚本批量替换+校验 → build+restart+双验证 → 回写 skill。

## 八、组合性说明

- 每阶段独立可验证、可单独 commit/回滚；阶段 1 内部各平台可并行。
- 若想"只要官方新功能先跑起来"：可只执行阶段 0 → 直接部署官方基线到 40（我们的功能后补），但 40 会短暂失去 auxiliary 路由（Hermes 依赖）——建议按完整顺序做。
- 节奏：每阶段完成 → 汇报验证结果 → 用户确认 → 进下一阶段。

---
*计划创建：2026-08-01 平行线。基于官方 76c3e6b / 我们 f23a553 实测 diff。*
