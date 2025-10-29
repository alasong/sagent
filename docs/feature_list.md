# 产品功能清单与演进计划（对外展示）

版本：v1.0.0（发布日期：2025-10-28）
项目：Agent

## 概述

- 面向企业级智能体应用的可扩展框架，已覆盖核心工具、路由与故障切换、统一输出契约、集中配置校验、异步重试策略与安全策略。
- 当前测试覆盖完整，40 项用例全部通过，具备对外演示与试点接入的稳定性。

## 已实现能力

- 路由与故障切换
  - 全局加权路由与工具级 `fallback_chain`。
  - 断路器与策略过滤（成本、能力、SLA 退化）。
- 核心工具能力
  - `web_fetch`：HTTP 拉取与文本预览。
  - `file_read`/`file_write`：本地文件读写（覆盖大小、覆盖标志）。
  - `list_dir`：目录列举（限制条目数）。
  - `open_app`：打开应用（带参数）。
  - `web_search`：来源可选、限速与最大返回数。
  - `web_scrape`：基本页面抓取与标题、正文提取。
  - `search_aggregate`：多源搜索聚合与去重。
- 工具发现与调度
  - 自动发现工具 Schema，统一 `TOOL_HANDLERS` 与 `run_tool()`。
  - 提供异步版本 `ASYNC_TOOL_HANDLERS` 与 `async_run_tool()`。
- 输出契约统一
  - 统一的 `normalize_tool_result()` 与 `OutputContract`，对齐 `config/policies/output_schema.json`。
  - 保证 `answer/citations/tool_used/tool_result` 的结构化一致性。
- 集中配置加载与校验
  - `scripts/config_loader.py` 提供缓存化的 `registry/routing/guardrails/output_schema/tool_policies`。
  - `scripts/validate_config.py` 提供集中校验 `validate_all()`。
- 安全与守卫策略
  - `run_command` 白名单与超时、`web_search` 限速与最大返回数。
  - 审计事件时间线与会话日志（JSONL）。
- 测试与质量保障
  - 40 项自动化测试涵盖路由、策略、工具行为、时间线、Schema 校验等。

## 关键架构亮点

- 配置中心化：所有核心配置统一加载，支持缓存与默认回退。
- 契约优先：输出统一抽象便于上层消费与跨工具聚合。
- 面向策略的执行：成本、能力、延迟与退化策略贯穿工具执行全链路。
- 异步与重试：网络类工具提供异步实现，内置指数退避与有限重试。

## 工具清单（概览）

- 已实现：`web_fetch`、`file_read`、`web_search`、`run_command`、`web_scrape`、`file_write`、`list_dir`、`open_app`、`search_aggregate`
- 统一契约支持：上述工具均通过 `normalize_tool_result` 映射到统一结构。
- 路由与策略：`config/routing.yaml` 提供全局与工具级策略、能力要求与成本约束。

## 配置与策略（示例）

- 模型注册：`config/models/registry.yaml`（默认提供方与能力、成本配置）。
- 路由策略：`config/routing.yaml`（全局权重、`fallback_chain`、工具级策略）。
- 输出契约：`config/policies/output_schema.json`（对外 JSON 结构约束）。
- 守卫策略：`config/policies/guardrails.yaml`（限速、白名单、审批等）。

## 异步与重试策略

- 异步工具：`async_tool_web_fetch`、`async_tool_web_scrape`、`async_tool_web_search`。
- 退避重试：指数退避（例如 0.5→1→2s），最大重试次数受策略与实现限制。
- 断路器：失败阈值与冷却期可配置，半开状态试探后成功即闭合。

## 安全与合规

- 命令执行白名单与超时控制，默认拒绝不在白名单的命令。
- 搜索限速与条目上限，防止外部接口滥用与成本失控。
- 日志与审计：时间线事件与会话级 JSONL 记录可用于追踪与合规审计。

## 测试与交付质量

- 自动化测试：40 项全部通过（功能、策略、路由、输出契约、时间线）。
- 回归保障：变更后可通过 `pytest -q` 快速验证核心能力。

## 接入与集成

- CI 集成：可在 `.github/workflows/ci.yaml` 中加入 `python scripts/generate_progress.py` 以自动更新进度文档。
- 统一入口：`scripts/poc_local_validate.py` 提供工具执行、规划与输出结构化。

## 后续演进计划（Roadmap）

- 审批拦截与人审流程
  - 在提交高风险动作（执行命令、写文件、打开应用）前，支持审批拦截与多级审核。
- 统一审计日志与指标
  - 统一标准化审计事件模型，接入指标上报（如调用量、失败率、延迟分布）。
- 安全行为测试套件
  - 针对限速、审批、黑白名单的自动化行为测试与场景覆盖。
- 超时与退避策略细化
  - 基于工具级 `tool_policies` 动态设定最大重试、超时与退避曲线。
- 输出契约扩展
  - 针对更多工具类型完善 `normalize_tool_result` 的映射与验证规则。
- 可观测性增强
  - 更细粒度的时间线事件、错误分类与跨会话统计分析。

## 里程碑（建议）

- M1（本月）：审批拦截与人审 MVP、审计事件模型初版。
- M2（下月）：安全行为测试套件与指标上报集成、策略细化。
- M3（两个月内）：可观测性增强、更多工具契约拓展与性能优化。

## 兼容性与限制

- 当前以本地验证为主，外部调用能力受各提供方配置与网络条件影响。
- 审批与监管能力为规划中，适用于企业落地场景需结合内网与安全要求。

---

如需演示或试点接入，请联系项目维护者以获取环境与配置说明。

