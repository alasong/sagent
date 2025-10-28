# SAgent 发布说明 v1.0.0

版本：v1.0.0  
发布日期：2025-10-28

## 概述
这是 SAgent 的首个稳定版本，核心链路（工具→路由→统一输出契约→策略守卫→异步重试→日志与测试）已打通，支持直接进行二次开发与试点接入。所有现有测试通过（40/40），并提供自动化进度文档与对外功能清单。

## 核心能力
- 统一输出契约（OutputContract）：统一工具输出结构，JSON Schema 校验（`config/policies/output_schema.json`）。
- 集中式配置加载（ConfigLoader）：对 YAML/JSON 配置进行缓存与合并（`scripts/config_loader.py`）。
- 工具路由与故障切换：基于 `config/routing.yaml` 的主路由、回退链与降级策略。
- 异步与重试策略：提供异步工具与指数退避重试，支持按工具策略动态调整（`guardrails.yaml`）。
- 策略守卫（Guardrails）：全局与工具级安全/限制策略（黑白名单、超时、重试）可配置。
- 事件时间线与日志：可视化事件序列与运行日志（`logs/poc_timeline.log`、`scripts/timeline_view.py`）。
- 自动化进度与外部文档：`scripts/generate_progress.py` 刷新 `docs/progress.md`；`docs/feature_list.md` 对外功能清单。

## 包含的工具（按检测与配置）
- 已实现：`web_fetch`、`web_search`、`web_scrape`、`file_read`、`file_write`、`list_dir`、`open_app`、`run_command`、`calc`、`search`、`search_aggregate`、`summarize`、`translate`
- 说明：具体工具的可用性以 `config/routing.yaml` 与策略配置为准，均需通过 `OutputContract` 返回统一结构。

## 主要文件与清单（Manifest）
- 版本文件：`VERSION`（当前为 `1.0.0`）
- 配置：
  - `config/models/registry.yaml`
  - `config/routing.yaml`
  - `config/policies/guardrails.yaml`
  - `config/policies/output_schema.json`
  - `config/prompts/base_system.txt`
  - `config/tools/schema/`（如需工具级 schema）
- 脚本与能力：
  - `scripts/config_loader.py`（集中式配置与策略合并）
  - `scripts/poc_local_validate.py`（OutputContract 使用示例）
  - `scripts/generate_progress.py`（完成度检测与进度文档刷新）
  - `scripts/routing_explain.py`（路由解释，可选）
  - `scripts/timeline_view.py`（事件时间线，可选）
  - `scripts/validate_config.py`（配置校验）
- 测试：`tests/`（路由、契约、策略、重试、降级、时间线、配置校验等）
- 文档：
  - `docs/feature_list.md`（外部功能清单与路线图）
  - `docs/progress.md`（完成度）
  - `docs/dev_guide.md`（二次开发指导）
  - `docs/release_notes_v1.0.0.md`（当前发布说明）

## 变更概览（v1.0.0）
- 新增：集中式配置加载与缓存（ConfigLoader）
- 新增：统一输出契约与 JSON Schema 校验（OutputContract）
- 新增：异步工具与指数退避重试策略（含同步包装）
- 新增：自动化进度生成与推荐项检测（generate_progress）
- 新增：外部功能清单与二次开发指导文档（feature_list/dev_guide）
- 修复：进度脚本 `UnboundLocalError`（推荐项检测逻辑调整）

## 兼容性
- Python：建议 `3.11+`（当前在 `3.13` 环境验证通过）
- 操作系统：Windows/macOS/Linux（注意各自的命令差异与依赖）
- 依赖：`requirements.txt` 中列出；安装后运行测试确保兼容性。

## 已知限制与后续计划
- 审批拦截与人审流程：尚未统一接入，建议通过 Hook 渐进落地。
- 统一审计日志与指标：待统一事件模型与归集方案。
- 安全行为测试：限速/审批/黑白名单等用例计划补充。

## 升级与迁移指引（从预发布到 v1.0.0）
- 输出契约：所有工具输出需通过 `OutputContract.normalize_and_validate`；如包含新增字段，请同步修改 `output_schema.json`。
- 策略合并：建议通过 `ConfigLoader.tool_policies(tool)` 动态获取超时与重试参数，替代硬编码。
- 路由与回退：为关键任务配置 `fallback_chain` 与 `degrade_policy`，提升鲁棒性。

## 验证步骤（推荐）
1. 安装依赖：`pip install -r requirements.txt`
2. 运行测试：`pytest -q`（预期全部通过）
3. 刷新进度：`python scripts/generate_progress.py`（更新 `docs/progress.md`）
4. 查看文档：`docs/dev_guide.md`、`docs/feature_list.md`、`docs/progress.md`

## CI 集成建议
- 在 `.github/workflows/ci.yaml` 中：
  - 运行 `pytest -q`
  - 执行 `python scripts/validate_config.py` 校验配置完整性
  - 执行 `python scripts/generate_progress.py` 刷新进度文档
  - 可选择将 `docs/progress.md` 与 `docs/release_notes_v1.0.0.md` 作为构建工件

---
如需演示或试点接入，请联系项目维护者以获取环境与配置说明。
