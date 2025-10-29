# 七步闭环实施形态选择：网站平台 vs 命令行（分析）

> 目标：在“意图 → 条款 → 自动处理 → 验证 → 微调 → 发布”的七步闭环中，选择最优的实现形态。原则是平台管治理与编排、Agent管领域推理与产出，体验最少打扰、契约统一、可审计可复用。

## 背景与目标
- 将复杂度收敛在平台（治理、编排、合规、成本、审计），将智能集中在 Agent（解析、生成、自查）。
- 统一输入/输出契约（JSON 工件 + Markdown 报告），同时支持本地开发、CI 与团队协作。

## 对比维度
- 用户体验与协作：一页式总览、审批流、多人角色协同。
- 治理与合规：预算阈值、外部调用审批、审计日志与报表。
- 自动化与集成：流水线、触发式询问、回滚与重试、观测与告警。
- 复用与规模：模板库、Prompt库、工具注册、Agent编排与市场化。
- 成本与复杂度：搭建成本、运维负担、团队能力与速度。

## 网站平台（Web UI）
- 优点：
  - 一页式确认书与进展看板，信息密度高、低打扰。
  - 审批与合规治理（外部调用授权、预算阈值、合规白名单）。
  - 多人协作与角色权限、审计日志与报表、统一体验。
  - 路由/成本/SLA统一管控，多 Agent 编排可视化，发布控制台。
- 适用：
  - 团队/企业级、多个项目/Agent 并行、合规要求较高、需要治理与审计。
- 代价：
  - 初始建设（后端服务、数据库、权限安全、观测体系）、持续运维成本。

## 命令行（CLI）
- 优点：
  - 轻量快速，开发者友好；易脚本化，适合 CI/CD；可离线，无前端依赖。
  - 与现有脚本和测试天然协同：`scripts/*`、`tests/*`。
- 适用：
  - 本地验证、单人/小团队、POC、自动化流水线。
- 代价：
  - 多人协作与审批体验弱，审计可视化差；需额外规范输出与日志，才能被平台消费。

## 推荐：混合方案（平台 + CLI + Agent）
- 职责分工：
  - 平台：编排与治理、审批与审计、成本与SLA、版本与发布、统一 UI。
  - Agent：意图解析与条款填充、结构化生成（PRD/Stories/NFR/Acceptance/Risks/Dependencies）、自验证与差异建议、验收报告生成。
  - CLI：开发者入口与 CI 集成，作为平台能力的“薄皮”与自动化接口。
- 契约统一：
  - 数据工件：`prd.json / stories.json / nfr.json / acceptance.json / risks.json / dependencies.json` + 报告（Markdown）。
  - 平台与 CLI 共享同一服务/库，避免双栈重复实现。
- 能力映射：
  - CLI 子命令（建议）：`intent-parse`、`terms-generate`、`validate`、`accept`、`progress`、`release`。
  - 平台模块（建议）：一页式确认、进展看板、审批与预算治理、审计与报表、发布控制台、Agent 市场与编排。

## 渐进落地路线
- Phase 0（CLI 最小闭环）：
  - 用现有 `scripts` 和 `tests` 跑通：条款生成/校验、进展快照、验收报告、版本推进与发布。
- Phase 1（轻平台）：
  - 单页确认 + 进展看板 + 审批/预算治理；后端复用 CLI 能力与服务层。
- Phase 2（云化工作流）：
  - 多租户、多 Agent 编排、合规与成本治理、审计与报表、观测与告警。
- Phase 3（生态化）：
  - 模板库、Prompt库、工具注册与市场、多 Agent 协作策略与 A/B 评估。

## 映射到当前仓库
- CLI/服务可直接复用：
  - 校验与契约：`scripts/domain_validate.py`、`scripts/validate_config.py`、`config/policies/output_schema.json`。
  - 路由与策略：`scripts/routing_explain.py`、`config/routing.yaml`、`config/models/registry.yaml`。
  - 进展与时间线：`scripts/generate_progress.py`、`scripts/timeline_view.py`。
  - 发布与版本：`scripts/make_release.py`、`.github/workflows/release.yaml`、`VERSION`、`CHANGELOG.md`。
- 文档与模板：
  - 七步流程：`docs/agent_flow_7_steps.md`
  - 条款模板与示例：`docs/templates/software_dev_terms_template.md`、`docs/examples/*`

## 决策建议
- 先用 CLI 打通闭环（验证门槛与工件契约），随后上线轻平台做团队协作与治理；保持统一 JSON 契约与报告，避免重复实现。

## 风险与应对
- 双栈重复实现：共享同一服务/库层；CLI 与 Web 只做壳层。
- 合规与成本：平台强制预算阈值与降级策略；外部调用审批白名单与审计日志。
- 用户过载：坚持一页式总览与触发式询问；非必要不打扰。

