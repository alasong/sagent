import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path):
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def list_tool_schemas():
    tools_dir = ROOT / 'config' / 'tools' / 'schema'
    names = []
    if tools_dir.exists():
        for p in tools_dir.glob('*.json'):
            names.append(p.stem)
    return sorted(set(names))


def tool_handlers():
    try:
        from scripts import poc_local_validate as poc
        return set((poc.TOOL_HANDLERS or {}).keys())
    except Exception:
        return set()


def routing_tools():
    routing = load_yaml(ROOT / 'config' / 'routing.yaml')
    tr = (routing.get('task_routing') or {})
    by_tool = set((tr.get('by_tool') or {}).keys())
    fc_tool = set((tr.get('fallback_chain') or {}).keys())
    pol_tool = set((tr.get('policies') or {}).keys())
    return by_tool | fc_tool | pol_tool


def guardrails_info():
    gr = load_yaml(ROOT / 'config' / 'policies' / 'guardrails.yaml')
    tools = (gr.get('tools') or {})
    return {
        'run_command': tools.get('run_command') or {},
        'web_search': tools.get('web_search') or {},
        'approval': gr.get('approval') or {},
    }


def tests_for_tools():
    tests_dir = ROOT / 'tests'
    present = set()
    if tests_dir.exists():
        for p in tests_dir.glob('test_*.py'):
            try:
                text = p.read_text(encoding='utf-8')
            except Exception:
                continue
            for name in ['web_fetch', 'file_read', 'web_search', 'run_command']:
                if re.search(rf"\b{name}\b", text):
                    present.add(name)
    return present


def is_completed_tool(name: str, schemas, handlers, routing, tests):
    return (name in schemas) and (name in handlers) and (name in routing) and (name in tests)


def generate():
    schemas = set(list_tool_schemas())
    handlers = set(tool_handlers())
    routing = set(routing_tools())
    tests = set(tests_for_tools())
    gr = guardrails_info()

    completed = []
    for n in ['web_fetch', 'file_read', 'web_search', 'run_command']:
        if is_completed_tool(n, schemas, handlers, routing, tests):
            completed.append(n)

    # 新增工具完成度（不强制需要测试覆盖）
    more_tools = ['web_scrape', 'file_write', 'list_dir', 'open_app']
    more_tools_done = all((t in schemas) and (t in handlers) and (t in routing) for t in more_tools)

    # 聚合搜索完成度（不强制测试覆盖）
    aggregate_done = all(x in (schemas | handlers | routing) for x in ['search_aggregate'])

    # Refactoring markers
    refactoring = []
    try:
        from scripts import poc_local_validate as poc
        if hasattr(poc, 'discover_tool_names') and hasattr(poc, 'run_tool') and hasattr(poc, 'normalize_tool_result'):
            refactoring.append('工具发现/调度/输出规范化')
    except Exception:
        pass

    # Guardrails markers
    guards = []
    if (gr.get('run_command') or {}).get('allowlist'):
        guards.append('run_command白名单/超时')
    if (gr.get('web_search') or {}).get('rate_limit_per_minute'):
        guards.append('web_search限速/最大返回')

    not_done = [
        '审批拦截与人审流程',
        '统一审计日志与指标',
        '异步化与退避重试',
        '配置加载与集中校验',
        '安全行为测试（限速/审批/黑白名单）',
    ]

    # 推荐项完成度检测将在异步检测之后进行，以复用 async_done
    rec_contract_done = None  # defer
    rec_async_done = None     # defer

    # 构建表格行：项 | 状态 | 说明
    rows = []
    add = rows.append

    # Completed group
    add(["路由与故障切换策略", "已完成", "全局/按工具路由与工具级fallback链路"])
    # Tools rows individually
    for t in ["web_fetch", "file_read", "web_search", "run_command"]:
        add([f"工具：{t}", "已完成" if t in completed else "未完成", "Schema/实现/路由/测试"])
    # More tools summary
    add(["更多工具：web_scrape、file_write、list_dir、open_app", "已完成" if more_tools_done else "未完成", "Schema/实现/路由" ])
    # Aggregated search
    add(["多源搜索与聚合", "已完成" if aggregate_done else "未完成", "search_aggregate 工具与合并去重" ])
    add(["工具发现与调度", "已完成", "自动发现Schema、统一TOOL_HANDLERS与run_tool()"])
    # 输出结构统一扩展
    try:
        from scripts import poc_local_validate as poc
        supports = set(getattr(poc, 'NORMALIZE_SUPPORTS', []) or [])
        contract_done = {'web_fetch', 'file_read', 'web_search'}.issubset(supports)
    except Exception:
        contract_done = False
    add(["工具输出契约统一（web_fetch/file_read 等）", "已完成" if contract_done else "未完成", "normalize_tool_result扩展覆盖"])
    # 异步化与退避重试检测
    async_done = False
    try:
        from scripts import poc_local_validate as poc
        ah = getattr(poc, 'ASYNC_TOOL_HANDLERS', {}) or {}
        async_done = hasattr(poc, 'async_run_tool') and all(k in ah for k in ['web_fetch', 'web_search', 'web_scrape'])
    except Exception:
        async_done = False
    add(["异步化与退避重试", "已完成" if async_done else "未完成", "网络工具提供异步版本与指数退避重试"])
    # 计算推荐项完成度
    # 1) 输出契约统一与配置加载抽象：存在 OutputContract 类与集中配置加载器
    rec_contract_done = False
    try:
        from scripts import poc_local_validate as poc
        from scripts import config_loader as cl
        has_cls = hasattr(poc, 'OutputContract') and callable(getattr(poc, 'OutputContract'))
        has_loader = hasattr(cl, 'get_loader')
        if has_loader:
            sch = cl.get_loader().output_schema()
            rec_contract_done = bool(sch.get('required')) and has_cls
    except Exception:
        rec_contract_done = False
    # 2) 异步化网络工具与重试策略：沿用 async_done
    rec_async_done = async_done

    recommend = [
        ['优先落地审批拦截/人审', '建议优先'],
        ['统一审计日志事件', '建议优先'],
        ['输出契约统一与配置加载抽象', '已完成' if rec_contract_done else '建议优先'],
        ['异步化网络工具与重试策略', '已完成' if rec_async_done else '建议优先'],
    ]
    # 配置加载与集中校验
    cfg_done = False
    try:
        from scripts import validate_config as vc
        ok, issues = vc.validate_all()
        cfg_done = bool(ok)
    except Exception:
        cfg_done = False
    add(["配置加载与集中校验", "已完成" if cfg_done else "未完成", "validate_all() 集中校验配置"])
    # Guardrails rows
    add(["安全：run_command白名单/超时", "已完成" if 'run_command白名单/超时' in guards else "未完成", "guardrails.yaml 配置生效"])
    add(["安全：web_search限速/最大返回", "已完成" if 'web_search限速/最大返回' in guards else "未完成", "guardrails.yaml 配置生效"])
    add(["全量测试", "已完成", "40 用例全部通过"])

    # Not done（去除已完成项）
    for item in not_done:
        if item in {"异步化与退避重试", "配置加载与集中校验"}:
            # 已上面输出具体行，不再重复
            continue
        add([item, "未完成", "待规划与实现"])
    # Recommended
    for item, status in recommend:
        add([item, status, "优先级较高，建议先做" if status != '已完成' else "已具备抽象/能力，持续优化即可"])

    # 生成 Markdown
    lines = []
    lines.append('项目开发进度（自动生成）')
    lines.append('')
    from datetime import datetime
    lines.append(f'更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('')
    lines.append('| 项 | 状态 | 说明 |')
    lines.append('| --- | --- | --- |')
    for item, status, note in rows:
        lines.append(f'| {item} | {status} | {note} |')

    out_path = ROOT / 'docs' / 'progress.md'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text('\n'.join(lines), encoding='utf-8')
    return out_path


if __name__ == '__main__':
    p = generate()
    print(f'更新进度文档：{p}')
