# Demo Guide

## Test Cases

| Input | Expected |
|-------|----------|
| Pay $25 to api.openai.com | ALLOW |
| Send $200 to api.openai.com | DENY (cap) |
| Pay $10 to scam-vip.com | DENY (blocked) |
| Send $15 to randomvendor.com | DENY (not allowlisted) |
| Pay $35 to anthropic.com | REQUIRE_APPROVAL |
