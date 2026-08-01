# Provider 增删架构规范（PROVIDERS.md）

> **状态**：v1.0，2026-08-01 用户确认（"后面我们会出现 provider 增加和移除的操作，应该被提前规划好"）
> **适用范围**：本仓库（freellmapi-auxiliary，合并官方 v0.6.6 后的合体版）所有 provider 的增、删、改
> **强制要求**：任何 provider 变更必须按本文档执行。opencode 编码时必须遵守（AGENTS.md 第 8 节同步此规范）。

## 0. 设计原则：4 层架构

| 层 | 内容 | 负责人 |
|---|---|---|
| **代码层** | provider 注册、路由、key 解析（跟官方架构走） | opencode |
| **模型层** | 模型入库、防删、退役（catalog-sync + key_id 绑定） | opencode + Hermes 验收 |
| **知识层** | `docs/PROVIDERS.md` 清单（每平台免费规则/模型/状态） | Hermes 维护 |
| **流程层** | 增删 SOP + 免费判定标准（本文档 + skill 同步） | 全员遵守 |

## 1. 代码层规范

### 1.1 注册方式（跟官方，不自己造）
- 所有 provider 集中在 `server/src/providers/index.ts`，用 `Map<Platform, BaseProvider>` + `register()`。
- OpenAI 兼容平台用 `OpenAICompatProvider`（一个类覆盖多数平台）；特殊协议（如 OpenModel 的 Anthropic Messages）用独立类。
- **删除平台必须留注释**记录原因（官方风格，如 SambaNova dropped 注释）：`// <platform> was dropped in <date>: <原因>`。

### 1.2 timeout 机制
- **代码里不硬编码大 timeout**。官方 v0.6.6 用 `lib/provider-timeout.ts` 的 `PROVIDER_TIMEOUT_<PLATFORM>` 环境变量。
- 推理模型（agnese-2.5-pro-alpha 等）非流式单次 60-120s 是常态 → 部署时设环境变量：
  ```bash
  PROVIDER_TIMEOUT_AGNES=120000 PROVIDER_TIMEOUT_NARA=120000  # 40 部署时 systemd Environment=
  ```

### 1.3 新增 provider 需要改的代码点（全量清单）
1. `server/src/providers/index.ts` — `register(new ...)`（核心）
2. `server/src/lib/key-parser.ts` — `PREFIX_MAP` 加 key 前缀（如 `sk-nry-` → bynara）
3. `server/src/routes/keys.ts` — `PLATFORMS` 列表加平台
4. `shared/types.ts` — `Platform` union 加平台
5. `client/src/pages/KeysPage.tsx` — 加 UI 条目
6. （特殊协议）`server/src/providers/<platform>.ts` — 独立 provider 类

## 2. 模型层规范（防删铁律）

- **官方 catalog 内模型**：catalog-sync 每 12h 自动同步（Ed25519 验签），增删自动，**不要手工干预**。
- **本地扩展平台模型**（bynara/nara/agnes/aiand 等不在 catalog 的）：
  - **必须 `key_id` 绑定**（`models.key_id` 指向 api_keys.id）——catalog-sync 只删 `key_id IS NULL AND size_label NOT IN ('User','Custom')` 且不在 catalog 的行
  - 或 `size_label='Custom'` 双保险
- **退役模型**：官方有 tombstone 墓碑机制（`model-state.ts`），可标记可恢复；本地模型退役 → 直接从 models 表删 + 清 auxiliary_config 引用。
- **删模型前**必须检查 `auxiliary_config` 是否有引用（`DELETE FROM auxiliary_config WHERE model_db_id NOT IN (SELECT id FROM models)` 清理孤儿）。

## 3. 知识层：平台清单（PROVIDERS.md 核心表）

> 维护规则：每次增/删/改 provider 后**必须更新本表**。status: active / degraded / dropped。

| 平台 | 端点 | key 前缀 | 免费规则（额度/RPM） | 免费模型 | 状态 | 特殊配置 |
|---|---|---|---|---|---|---|
| agnes | https://apihub.agnes-ai.com/v1 | sk- | 无文档 RPM（免费额度） | agnes-2.0-flash, 2.5-flash, 2.5-pro-alpha, agnes-image | active | **要 key**（非 keyless）；timeout 120s（env PROVIDER_TIMEOUT_AGNES）；推理模型非流式 60-120s |
| nara | https://router.bynara.id/v1 | sk-nry- | 免费计划 700万 token/日 + 10 RPM | agnes-2.0/2.5-flash, mistral-large, mistral-medium-3-5, nemotron-3-ultra, stepfun-3.7-flash | active | NaraRouter 双入口之一；官方 v0.6.6 自带 |
| bynara | https://router.bynara.id/v1 | sk-nry- | 同上（同后端） | 同上 | active | **与 nara 同后端双入口**，不重复添加（用户确认 2026-08-01） |
| opencode zen | https://opencode.ai/zen/v1 | OPENCODE_ | 促销模型 | 促销模型 | active | — |
| openmodel | https://api.openmodel.ai/v1 | om- | **全付费**（无免费） | 无 | degraded | Anthropic Messages 协议（OpenModelMessagesProvider）；已移植但需 key 验证 |
| aiand | https://api.aiand.com/v1 | sk- | **预付制**：$0 余额全 404（最低 $5 绑卡） | qwen/qwen3.6-27b（文档标 Free 已过期） | **dropped** | 弃用原因：预付制坑；替代：qwen3.6-27b 走 groq 免费 |
| groq | https://api.groq.com/openai/v1 | gsk_ | 免费 tier | qwen3.6-27b 等 | active | aiand 的替代 |
| openrouter | https://openrouter.ai/api/v1 | sk-or- | :free 模型 | 大量 :free | active | 官方自带 |
| mistral | https://api.mistral.ai/v1 | — | 免费 tier | mistral-* | active | 官方自带 |
| nvidia | https://integrate.api.nvidia.com/v1 | nvapi- | 免费 tier | deepseek-v4-pro 等 | active | timeout 180s（官方）；forceSingleToolCall |
| zhipu | open.bigmodel.cn | — | 免费额度 | glm-* | active | 官方自带 |
| github | models.github.ai | github_pat_ | GitHub Models | 厂商/模型 | active | 官方自带 |
| modelscope | （官方） | — | 50+ 免费模型 | qwen/deepseek/glm | active | 官方 v0.6.6 新增（我们不需移植） |
| pollinations | （官方） | — | 免费 | — | active | 官方 v0.6.6 新增 |

> 官方 v0.6.6 其他自带平台：ainative, aion, bazaarlink, cerebras, custom, huggingface, kilo, llm7, navy, ollama, ovh, reka, requesty, routeway, sealion, siliconflow。（这些官方已管理，如无特殊需求不动。）

## 4. 流程层：增删 SOP

### 4.1 增加 provider（7 步）
1. **调研免费规则**：查端点 / key 格式 / 免费额度 / RPM / 模型列表（调上游 /v1/models）
2. **判定免费**：真免费（pricing=0 或免费 tier 无需卡）vs **预付制坑**（$0 全 404，需绑卡充值）——预付制**不接入**，找替代（如 aiand→groq）
3. **代码层**：按 §1.3 的 6 点改（index.ts 注册 / key-parser / keys.ts / types.ts / KeysPage）
4. **模型入库**：调上游 models API → INSERT models 表（intelligence_rank/speed_rank/size_label 必填）→ **key_id 绑定**（防 catalog-sync 删）
5. **实测验证**：上游 chat 200 + 流式 + 非流式（推理模型慢则配 PROVIDER_TIMEOUT_）
6. **更新 PROVIDERS.md 清单**（§3 表加行）
7. **commit**：独立 commit（`feat(provider): <platform>`），可单独回滚

### 4.2 移除 provider（6 步）
1. **确认移除原因**：免费转收费 / 平台倒闭 / 预付制坑 / 上游杀模型
2. **代码层**：index.ts 删 register（**留注释**记录原因和日期）→ key-parser 删前缀 → keys.ts / types.ts / KeysPage 清理
3. **key 停用**：`UPDATE api_keys SET enabled=0 WHERE platform='<platform>'`（保留数据可恢复，不硬删）
4. **模型处理**：删除 models 表该平台行（或保留 size_label='Custom' 冻结）→ **清 auxiliary_config 孤儿引用**
5. **更新 PROVIDERS.md 清单**：status 改 dropped + 原因
6. **commit**：独立 commit（`feat(provider): drop <platform>`）

### 4.3 免费判定标准
| 类型 | 判定 | 处置 |
|---|---|---|
| 真免费 | pricing=0 或免费 tier 无卡 | ✅ 接入 |
| 近似免费 | $0 小额或 trial | ⚠️ 标记 degraded，评估 |
| 预付制 | $0 余额全 404，需充值 | ❌ 不接入，找替代 |
| 已转收费 | 原免费变付费 | ❌ 移除或保留 key 停用 |

## 5. opencode 编码须知（编码时记得）
- 任何 provider 增删改动：**先读本文档 §1-§4**，按 SOP 执行，禁止跳过任意步骤（尤其模型 key_id 绑定和 PROVIDERS.md 更新）。
- 代码层只改该平台相关文件，**不动官方已有其他平台**。
- 删除平台必须留注释原因（官方风格）。
- 模型入库 4 字段必填：intelligence_rank / speed_rank / size_label / key_id。
- 不确定的免费规则**先实测**（调上游 API），不臆测。

---
*v1.0，2026-08-01。基于 freellmapi-devops skill 实测经验 + 官方 v0.6.6 架构调研。*
