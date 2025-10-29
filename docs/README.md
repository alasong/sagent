# 文档索引（Docs Index）

- 模板与确认书
  - 软件研发类必要条款模板（含示例确认书）：`docs/templates/software_dev_terms_template.md`
  - 示例条款确认书（Alpha）：`docs/examples/alpha_terms_confirmation.md`

- 过程与方法
  - Agent 开发与发布流程（完备版）：`docs/agent_release_flow.md`
  - 软件研发类 Agent 七步闭环流程：`docs/agent_flow_7_steps.md`
  - 七步闭环实施形态选择：网站平台 vs 命令行：`docs/platform_vs_cli_choice.md`

- 域模型与配置（参考）
  - 需求与产出结构：`config/domain_schema/*.json`
  - 路由与策略：`config/routing.yaml`
  - 输出校验：`config/policies/output_schema.json`
  - 系统基线提示：`config/prompts/base_system.txt`

- 脚本工具（可选）
  - 域模型校验：`scripts/domain_validate.py`、`scripts/validate_config.py`
  - 路由解释：`scripts/routing_explain.py`
  - 时间线视图：`scripts/timeline_view.py`
  - 进展生成：`scripts/generate_progress.py`

- 示例与演示
  - 进展快照（Alpha）：`docs/examples/alpha_progress_snapshot.json`
  - 验收清单（Alpha）：`docs/examples/alpha_acceptance_checklist.md`


项目：Agent

- 二次开发指南（Developer Guide）：`dev_guide.md`
- 对外功能清单（Feature List）：`feature_list.md`
- 发布说明（Release Notes v1.0.0）：`release_notes_v1.0.0.md`
- 项目进度（Progress）：`progress.md`

## 文档刷新与校验
- 刷新进度文档：`python scripts/generate_progress.py`
- 校验配置完整性：`python scripts/validate_config.py`
- 路由解释（可选）：`python scripts/routing_explain.py`
- 时间线视图（可选）：`python scripts/timeline_view.py`

## 发布与打包
- 本地生成发布包：`python scripts/make_release.py`
- 产物位置：`dist/agent-vX.Y.Z/` 与 `dist/agent-vX.Y.Z.zip`
- 自动发布（GitHub Actions）：推送标签 `vX.Y.Z` 即触发工作流 `.github/workflows/release.yaml`，自动构建并创建 Release，附件包含打包好的 ZIP。
- 示例：
  - 更新版本号：编辑 `VERSION` 为 `1.0.1`
  - 推送标签：
    - `git tag v1.0.1`
    - `git push origin v1.0.1`
  - 工作流步骤：安装依赖 → 校验配置 → 运行测试 → 生成进度 → 构建发布包 → 创建 GitHub Release（附 ZIP）

---
如需添加新文档，请在此索引注册，保持外部展示一致性。
