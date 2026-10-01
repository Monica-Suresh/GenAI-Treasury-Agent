import pytest
from guardrail.policy import SpendPolicy, SpendRequest
from guardrail.engine import PolicyEngine


@pytest.fixture
def engine():
    return PolicyEngine(SpendPolicy())


def test_allow_normal_payment(engine):
    result = engine.authorize(SpendRequest(
        agent_id="test", recipient="api.openai.com", amount=25.0, memo="credits"
    ))
    assert result["decision"] == "ALLOW"


def test_deny_over_cap(engine):
    result = engine.authorize(SpendRequest(
        agent_id="test", recipient="api.openai.com", amount=75.0, memo="bulk"
    ))
    assert result["decision"] == "DENY"


def test_deny_blocked_merchant(engine):
    result = engine.authorize(SpendRequest(
        agent_id="test", recipient="scam-vip.com", amount=10.0, memo="x"
    ))
    assert result["decision"] == "DENY"


def test_deny_not_allowlisted(engine):
    result = engine.authorize(SpendRequest(
        agent_id="test", recipient="unknown.com", amount=15.0, memo="y"
    ))
    assert result["decision"] == "DENY"


def test_require_approval(engine):
    result = engine.authorize(SpendRequest(
        agent_id="test", recipient="anthropic.com", amount=35.0, memo="z"
    ))
    assert result["decision"] == "REQUIRE_APPROVAL"
