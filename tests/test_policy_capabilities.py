from scripts import poc_local_validate as poc


def test_policy_allows_provider_requires_capabilities():
    # provider不具备long_context，策略要求时应拒绝
    provider_cfg = {"capabilities": ["function_call"]}
    policies = {"required_capabilities": ["long_context"]}
    allowed = poc.policy_allows_provider(provider_cfg, policies, est_tokens=1000)
    assert allowed is False

    # provider具备要求能力时允许
    provider_cfg2 = {"capabilities": ["function_call", "long_context"]}
    allowed2 = poc.policy_allows_provider(provider_cfg2, policies, est_tokens=1000)
    assert allowed2 is True

