from pydantic import BaseModel, Field
from typing import Optional


class SpendRequest(BaseModel):
    agent_id: str
    recipient: str
    amount: float
    memo: str = ""
    category: Optional[str] = None


class SpendPolicy(BaseModel):
    max_transaction: float = 50.0
    daily_budget: float = 100.0
    approval_threshold: float = 30.0
    allowed_merchants: list = Field(default_factory=lambda: [
        "api.openai.com", "anthropic.com", "aws.amazon.com"
    ])
    blocked_merchants: list = Field(default_factory=lambda: ["scam-vip.com"])
