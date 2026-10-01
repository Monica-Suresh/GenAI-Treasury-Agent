import uuid
from .policy import SpendPolicy, SpendRequest


class PolicyEngine:
    def __init__(self, policy: SpendPolicy):
        self.policy = policy
        self.spend_today = 0.0
        self.audit_trail = []

    def authorize(self, request: SpendRequest) -> dict:
        audit_id = str(uuid.uuid4())[:8]
        host = request.recipient.split("/")[0]

        if request.amount > self.policy.max_transaction:
            return self._log(audit_id, "DENY", "MAX_TRANSACTION_EXCEEDED",
                             f"Amount exceeds cap of {self.policy.max_transaction}")

        if host in self.policy.blocked_merchants:
            return self._log(audit_id, "DENY", "MERCHANT_BLOCKED",
                             f"{host} is blocked")

        if self.policy.allowed_merchants and host not in self.policy.allowed_merchants:
            return self._log(audit_id, "DENY", "MERCHANT_NOT_ALLOWLISTED",
                             f"{host} not allowlisted")

        if request.amount > self.policy.daily_budget - self.spend_today:
            return self._log(audit_id, "DENY", "DAILY_BUDGET_EXCEEDED",
                             "Daily budget exhausted")

        if request.amount >= self.policy.approval_threshold:
            return self._log(audit_id, "REQUIRE_APPROVAL", "APPROVAL_THRESHOLD",
                             "Requires human approval")

        self.spend_today += request.amount
        return self._log(audit_id, "ALLOW", "ALLOWED", "All checks passed")

    def _log(self, audit_id, decision, code, reason):
        entry = {"audit_id": audit_id, "decision": decision,
                 "reason_code": code, "reason": reason}
        self.audit_trail.append(entry)
        return entry
