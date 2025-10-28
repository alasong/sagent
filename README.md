# SAgent 框架（v1.0.0）

一个可用于本地验证与上线的通用 SAgent 框架，具备：工具路由与故障切换、统一输出契约（OutputContract）、集中式配置加载（ConfigLoader）、守卫策略（Guardrails）、事件时间线与测试/CI 基础。

- 当前版本：`v1.0.0`（对应 `VERSION` = 1.0.0）
- 发布说明：`docs/release_notes_v1.0.0.md`
- 变更日志：`CHANGELOG.md`

## 快速开始
- 环境：`python 3.11+`（当前本地 `3.13`）
- 安装依赖：`pip install -r requirements.txt`
- 运行测试：`pytest -q`
- 刷新进度文档：`python scripts/generate_progress.py`

## 关键文档
- 二次开发指南：`docs/dev_guide.md`
- 对外功能清单：`docs/feature_list.md`
- 发布说明（当前版本）：`docs/release_notes_v1.0.0.md`
- 进度与完成度：`docs/progress.md`

## 配置文件
- 路由：`config/routing.yaml`
- 守卫策略：`config/policies/guardrails.yaml`
- 输出契约：`config/policies/output_schema.json`
- 模型注册表：`config/models/registry.yaml`

## 目录结构（简要）
```
config/     # 配置（路由/策略/模型/提示词/工具契约）
docs/       # 文档（开发指南/功能清单/发布说明/进度）
scripts/    # 脚本（配置加载/验证/进度生成/路由解释/时间线视图）
tests/      # 测试用例（路由/契约/策略/重试/降级等）
```

## 发布包
- 本地打包脚本：`python scripts/make_release.py`
- 产物位置：`dist/agent-v1.0.0/` 与 `dist/agent-v1.0.0.zip`
- 清理临时与构建产物：使用 `git clean -xdf` 或参考 `/.gitignore` 项

## 许可与说明
- 本仓库内容可用于试点验证与二次开发。请结合企业内部合规策略进行发布与上线。
