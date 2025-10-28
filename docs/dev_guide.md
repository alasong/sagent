# 二次开发指导文档（Developer Guide）

版本：v1.0.0（发布日期：2025-10-28）
本开发指导文档已基于框架发布版本 v1.0.0 生成与校验。

> 适用范围：在当前框架基础上进行功能扩展、工具接入、策略配置、测试与上线。

## 概览
- 当前框架的核心能力已经完成并可用于二次开发：
  - 工具体系与路由、故障切换与降级、异步与重试策略
  - 统一输出契约（OutputContract）与集中式配置加载（ConfigLoader）
  - 策略与守卫（Guardrails）、事件时间线（Timeline）、测试与CI基础
- 仍在规划的治理特性：
  - 审批拦截与人审流程（可留接口进行渐进式接入）
  - 统一审计日志与指标归集（建议在试点后统一落地）
  - 安全行为测试（速率限制/审批/黑白名单）

以上治理模块不影响基本功能的二次开发与试点接入，可并行推进。

## 快速开始
- 环境准备：
  - `python` 版本建议 `3.11+`（当前项目运行于 `3.13`）
  - 安装依赖：`pip install -r requirements.txt`
  - 运行测试：`pytest -q`（验证基础功能与契约未破坏）
- 生成进度文档：`python scripts/generate_progress.py`（刷新 `docs/progress.md`）
- 查看对外功能清单：`docs/feature_list.md`

## 目录结构
```
config/
  models/registry.yaml          # 模型注册表
  policies/guardrails.yaml      # 策略与守卫（全局与工具级）
  policies/output_schema.json   # 统一输出契约 JSON Schema
  prompts/base_system.txt       # 系统提示词
  routing.yaml                  # 工具路由与故障切换
  tools/schema/                 # 工具输入/输出的 schema（如需）
docs/
  feature_list.md               # 对外功能清单（外部展示）
  progress.md                   # 进度与完成度
logs/
  poc.log / poc_timeline.log    # 运行日志与事件时间线
scripts/
  config_loader.py              # 集中式配置加载与缓存
  poc_local_validate.py         # 本地验证与 OutputContract 使用示例
  generate_progress.py          # 自动检测并生成进度文档
  routing_explain.py            # 路由解释（可选）
  timeline_view.py              # 事件时间线视图（可选）
  validate_config.py            # 配置完整性检查
```

## 核心组件与使用
- 集中式配置加载（ConfigLoader）
  - 入口：`scripts/config_loader.py`
  - 能力：缓存、YAML/JSON 读取、模型/路由/守卫/输出契约加载、`tool_policies(tool)` 合并全局与工具级策略
  - 示例：
    ```python
    from scripts.config_loader import ConfigLoader

    loader = ConfigLoader()
    output_schema = loader.load_output_schema()
    policies = loader.tool_policies("web_fetch")
    ```
- 统一输出契约（OutputContract）
  - 入口：`scripts/poc_local_validate.py`（示例类与用法）
  - 能力：输出结构归一化、字段校验与 JSON Schema 验证
  - 示例：
    ```python
    from scripts.poc_local_validate import OutputContract
    from scripts.config_loader import ConfigLoader

    loader = ConfigLoader()
    contract = OutputContract(schema=loader.load_output_schema())
    normalized = contract.normalize_and_validate({"tool": "web_fetch", "data": {...}})
    ```
- 路由与故障切换
  - 配置：`config/routing.yaml`
  - 能力：任务到工具的映射、优先级、回退链（fallback）、降级策略（degrade）
  - 建议：为新工具添加路由条目，并在关键路径上配置回退链以提升鲁棒性。
- 异步与重试策略
  - 框架支持异步版本工具与指数退避重试（含同步包装）。
  - 建议通过 `ConfigLoader.tool_policies(tool)` 读取每个工具的超时、重试次数与延迟等参数，实现动态调整。
  - `guardrails.yaml` 示例片段：
    ```yaml
    defaults:
      timeout_ms: 10000
      retry:
        max_attempts: 3
        base_delay_ms: 200
        jitter: true
    tools:
      web_fetch:
        timeout_ms: 12000
        retry:
          max_attempts: 4
          base_delay_ms: 300
    ```
- 守卫与安全策略（Guardrails）
  - 配置：`config/policies/guardrails.yaml`
  - 能力：黑白名单、速率限制、审批拦截（可留空实现/桩）
  - 建议：先按试点需要配置风险策略，后续再接入统一审计与审批流。

## 扩展新工具（步骤）
1. 定义输入/输出契约
   - 在 `config/tools/schema/` 或 `policies/output_schema.json` 中补充必要字段（尽量遵循现有结构）。
   - 若输出包含新增字段，需在 `output_schema.json` 中增加校验规则。
2. 实现工具逻辑
   - 在工具实现模块中添加处理函数（同步/异步均可）。
   - 输出通过 `OutputContract` 归一化并验证：
     ```python
     def tool_translate(text, target_lang):
         # ... 具体实现
         result = {"tool": "translate", "data": {"text": text, "lang": target_lang}}
         return contract.normalize_and_validate(result)
     ```
3. 路由与策略接入
   - 在 `config/routing.yaml` 为新工具添加路由规则与回退链。
   - 在 `guardrails.yaml` 中按需配置该工具的 `timeout_ms`、`retry`、白名单/黑名单等。
4. 本地验证与日志
   - 编写或补充测试（见下文），运行 `pytest -q`。
   - 通过 `logs/poc_timeline.log` 与 `scripts/timeline_view.py` 检查事件序列。
5. 进度文档更新
   - 运行 `python scripts/generate_progress.py`，确认 `docs/progress.md` 自动标记完成度。

## 路由配置示例（routing.yaml）
```yaml
routes:
  - task: "translate"
    primary: "translate"
    fallback_chain:
      - "web_fetch"
      - "summarize"
    degrade_policy:
      mode: "summary_only"
      note: "当翻译不可用时返回摘要降级"
```

## 测试与质量保障
- 单元测试位置：`tests/`（已包含路由、契约、策略、重试、降级等用例）
- 为新工具添加测试：
  - 契约与校验：字段存在性、类型、Schema 验证
  - 路由与回退：正确选择工具、故障时回退生效
  - 重试与超时：按 `tool_policies` 生效与日志可观测
- 运行：`pytest -q`

## CI 集成建议
- 工作流：`.github/workflows/ci.yaml`
- 建议增加：
  - 在测试后运行 `python scripts/generate_progress.py` 并将 `docs/progress.md` 作为工件或直接提交（按团队策略）
  - 对关键配置（`routing.yaml`、`guardrails.yaml`、`output_schema.json`）进行校验脚本 `scripts/validate_config.py`

## 审批与审计（规划）
- 审批拦截：在工具执行入口处预留 Hook（例如 `before_tool_exec`），按策略触发人审。
- 审计日志：统一事件模型与指标（如 `tool_invocation`, `retry_attempt`, `degrade_applied`），汇总到日志或指标系统。
- 安全测试：对速率限制、白/黑名单、审批流程进行行为测试用例设计。

## 常见问题（FAQ）
- 契约报错：检查 `output_schema.json` 是否包含新增字段；使用 `OutputContract.normalize_and_validate`。
- 路由未命中：确认 `config/routing.yaml` 中的 `task` 与调用时任务名一致。
- 重试不生效：检查 `guardrails.yaml` 中的 `retry` 合并结果，使用 `ConfigLoader.tool_policies(tool)` 调用后生效。
- 进度未更新：先运行测试；再执行 `python scripts/generate_progress.py` 刷新。

## 版本与发布建议
- 语义化版本：`MAJOR.MINOR.PATCH`
- 变更类型：工具新增、契约扩展、策略修改需在发布说明中标注影响范围与迁移指引。

---
如需演示或试点接入，请联系项目维护者以获取环境与配置说明。
