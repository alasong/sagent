# 云化 Agent 平台架构（先本地验证→云化上线）

发布日期：2025-10-27

## 目标与范围
- 目标：以本地最小可行验证为起点，演进到企业可用的云化 Agent 平台，兼顾可控性、可靠性、合规与成本。
- 范围：配置层（LLM/Tools/RAG）、框架层（记忆/执行抓手/业务流程引擎）、业务层（二次开发/可视化编排）、治理与观测（安全/审计/成本/SLO）。
- 非目标：绑定单一云厂商；一次性大跃迁（优先增量演进）。

## 分层架构（逻辑）
- 业务流层（编排与控制）：
  - Agent 状态图：LangGraph（分支、并行、重试、检查点）。
  - 长链路编排：Temporal/Flyte/Argo（补偿、回放、审计、调度）。
- 工具与执行层（多抓手）：
  - 工具协议：MCP/自研轻量接口（API/DB/浏览器/代码/RPA）。
  - 执行后端：Kubernetes Job/Service、Ray/Dask（并行计算/Actor）、Serverless（轻量任务）。
- 记忆与知识层：
  - 事件与状态：Postgres/Redis 事件存档（event-sourcing）。
  - 向量与检索：PGVector/Milvus；检索路由与索引用 LlamaIndex。
- 安全与治理层：
  - 身份与权限：OIDC/RBAC、工具白名单、数据边界、越权防护。
  - Guardrails：输出审核、内容安全策略、证据约束（RAG 引用）。
  - 成本与配额：预算、速率限制、并发治理（租户/项目维度）。
- 可观测与审计层：
  - 指标与追踪：OpenTelemetry、Prometheus/Grafana、分布式追踪。
  - 日志与回放：Loki/ELK，轨迹重放与任务级审计。

## LLM 大脑层与配置
- 模型注册与路由：
  - 模型注册表：提供者（OpenAI/Anthropic/Qwen/本地）、`model_name`、版本、上下文窗口、速率限制、成本指标。
  - 路由策略：基于能力（函数调用/长上下文/多模态）、延迟与成本的加权路由；故障转移与回退链（fallback）；金丝雀/灰度发布。
- 推理参数与模板：
  - 参数：`temperature`、`top_p`、`seed`、`response_format`、`tool_choice`、`max_tokens`、`stop`。
  - Prompt 管理：模板化与版本化（语料/系统指令/角色设定/工具描述），支持 A/B 实验与回滚。
- 工具协议与模式：
  - 函数/工具 Schema（JSON Schema），参数校验、必填与默认值、幂等与重试策略。
  - MCP 或统一工具接口层，规范鉴权与范围权限（Scopes）。
- RAG 配置与证据约束：
  - 索引策略（分块/嵌入模型/元数据）、检索器组合与路由（BM25+向量/Hybrid/多路召回）。
  - 证据约束：答案必须引用来源，支持反事实检测与事实一致性评估。
- 安全与合规：
  - 输入输出过滤：PII/合规词表、越权意图检测、越权工具拦截与提示升⼀级审批。
  - 身份映射：用户/服务账号到工具权限（RBAC/ABAC），审计可追踪到人/应用。
- 缓存与优化：
  - 语义缓存/检索缓存与路由热键；重复调用去重；成本预算与配额策略。
  - 失败恢复：重试退避、断点续跑、幂等键、补偿事务（外部系统）。
- 观测与评估：
  - 指标：`tokens_input`、`tokens_output`、`calls_total`、`latency_ms`、`cost_usd`、`tool_errors`。
  - 评估：离线基准/金标准任务集、轨迹回放、断言覆盖率、引用一致性、错误类型谱系。
- 目录与配置建议：
  - `config/models/registry.yaml`（模型源/速率/成本/功能标记）。
  - `config/routing.yaml`（路由权重/故障转移/灰度策略）。
  - `config/prompts/`（多场景模板与版本）。
  - `config/tools/schema/`（工具 JSON Schema 与鉴权）。
  - `config/policies/guardrails.yaml`（安全/合规/输出审核策略）。
  - `secrets/`（密钥与连接信息，受 KMS/Vault 管理）。


## Phase 0：本地最小可行验证（MVP）
- 技术栈（本地）：
  - 编排：LangGraph（Python）。
  - RAG：LlamaIndex（本地索引：FAISS/PGVector），数据用本地文档/CSV。
  - 存储：SQLite/轻量 Postgres（事件与任务记录）；可选 Redis 做缓存。
  - 执行：本地进程 + 可选 Ray 本地集群（单机并行）。
  - 可观测：本地日志 + 简易指标（Prometheus 本地/文件记录）。
- 场景用例（建议选一作为 PoC）：
  - 研究→生成→核查流水线：Researcher（检索/总结）→Writer（成稿）→Verifier（引用核查/断言）。
  - 代码代理：Issue→Plan→Implement→Test→Review 的受控迭代（含失败回退与断言）。
- 关键断言与评估：
  - 任务成功率、延迟、成本（Token）与检索一致性（引用可核查）。
  - 失败处理：重试策略、断点续跑、幂等与补偿路径。
- 本地目录结构（建议）：
  - `agents/`：角色定义与提示模板。
  - `tools/`：工具适配层（API/DB/Browser/Code）。
  - `workflows/`：LangGraph 状态图与编排节点。
  - `memory/`：事件存档与向量索引管理。
  - `eval/`：断言器与评估作业（成功率/一致性/成本）。
  - `infra/`：容器化与部署脚本（后续云化所需）。
  - `docs/`：设计说明与运行手册。

## Phase 1：云化路线与落地
- 路线 A（自管云原生，资源/业务分离）：
  - 资源层：Kubernetes（HPA/KEDA 自动扩缩）、Ray 集群（并行/Actor）。
  - 业务流层：LangGraph 负责 Agent 状态图；Temporal/Flyte/Argo 负责长链路编排与审计。
  - 数据与记忆：Managed Postgres/Redis；对象存储（S3/OSS）；向量库（PGVector/Milvus）。
  - 观测与治理：OpenTelemetry + Prom/Grafana + Loki；RBAC/Secret 管理（KMS/Vault）。
  - 优点：强可控与可审计、可移植、分层清晰；缺点：初始工程成本高。
- 路线 B（托管平台优先，快速交付）：
  - 国际：Vertex AI Agent Builder（ADK/Agent Engine）、Agents for Amazon Bedrock；编排可辅以 Prefect/Dagster Cloud。
  - 国内：百度文心 AgentBuilder（开发+分发+运营闭环）；工程可编排可用 AgentScope/Qwen-Agent + K8s。
  - 优点：交付快、治理与权限内建、运维压力低；缺点：厂商锁定与可移植性弱、细粒度控制有限。

## 云化部署流程（参考）
- 容器化：为 `agents/tools/workflows` 标准化镜像，分环境配置（dev/stage/prod）。
- CI/CD：构建/扫描/部署（GitHub Actions/GitLab CI），蓝绿/灰度发布与回滚。
- 配置与密钥：环境变量、密钥管理（KMS/Vault），按租户与项目隔离。
- 数据与隐私：VPC/子网隔离、数据驻留策略、加密传输与存储。
- 成本与配额：速率限制、并发控制、预算告警与限流（网关/队列）。

## SLO/指标与评估
- 成功率（任务级/节点级）、延迟分布、成本（Token/调用）、检索一致性（证据约束）。
- 审计覆盖率、失败类型谱系、重试/补偿效果、并发吞吐与资源利用率。

## 风险与缓解
- 厂商锁定：托管栈需抽象接口与迁移路径（双写/双部署阶段）。
- 工具越权与数据泄露：权限最小化、数据边界与日志审计、输出安全策略。
- 非确定性与错误连锁：断言与证据约束、回放强化、关键节点人审（HITL）。
- 调试复杂：统一追踪 ID、跨平面日志聚合、可重现的轨迹存档。

## 最小可行实施清单（起步到上线）
- 本地（2–4周）：
  - 选定 PoC 流水线（研究→写作→核查），实现 LangGraph 状态图与工具层。
  - 接入 LlamaIndex 与本地索引，完成证据约束与断言器。
  - 事件存档与基础评估（成功率/一致性/成本），本地日志与简易指标。
- 云化（4–8周）：
  - 容器化与 K8s/Ray 部署（或托管平台接入），完成 CI/CD 与密钥管理。
  - 接入可观测与审计；实现成本与配额治理，配置人审关卡。
  - 压测与SLO设定，按数据隐私与合规完成边界管理。

## 选型建议（速览）
- 追求强可控/审计：LangGraph + Temporal/Flyte + K8s/Ray + LlamaIndex。
- 快速交付与生态：Vertex Agent Builder / Bedrock Agents；编排用 Prefect/Dagster Cloud。
- 国内运营与分发：百度 AgentBuilder；工程可编排选 AgentScope/Qwen-Agent + K8s。

## 下一步
- 告诉我你的云环境偏好（AWS/GCP/国内）与场景（运营自动化/数据分析/客服/研发流水线），我将据此生成更具体的组件清单与目录骨架。
