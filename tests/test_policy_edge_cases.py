from guardrail.policy import SpendPolicy, SpendRequest
from guardrail.engine import PolicyEngine


def test_exact_cap_allowed():
    e = PolicyEngine(SpendPolicy(max_transaction=50.0))
    result = e.authorize(SpendRequest(
        agent_id="t", recipient="api.openai.com", amount=50.0, memo="exact"
    ))
    assert result["decision"] == "ALLOW"


def test_one_cent_over_cap_denied():
    e = PolicyEngine(SpendPolicy(max_transaction=50.0))
    result = e.authorize(SpendRequest(
        agent_id="t", recipient="api.openai.com", amount=50.01, memo="over"
    ))
    assert result["decision"] == "DENY"


def test_path_in_recipient_stripped():
    e = PolicyEngine(SpendPolicy())
    result = e.authorize(SpendRequest(
        agent_id="t", recipient="api.openai.com/v1/charges", amount=10.0, memo="p"
    ))
    assert result["decision"] == "ALLOW"
