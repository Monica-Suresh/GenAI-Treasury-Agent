import json
from langchain_core.messages import HumanMessage
from guardrail.policy import SpendRequest


def run_pipeline(user_input, guardrail, components, retriever):
    results = {"stages": {}}

    extraction_result = components["extraction_chain"].invoke({
        "user_input": user_input,
        "format_instructions": components["extraction_parser"].get_format_instructions(),
    })
    intents = [p.model_dump() for p in extraction_result.payments]
    results["stages"]["extraction"] = intents

    if not intents:
        results["stages"]["judgments"] = []
        results["stages"]["payments"] = []
        results["stages"]["summary"] = "No payment intents found."
        return results

    judgments = []
    for intent in intents:
        docs = retriever.invoke(intent["recipient"] + " " + intent.get("memo", ""))
        policy_context = "\n".join(d.page_content for d in docs)
        verdict = components["judge_chain"].invoke({
            "payment": f"${intent['amount']} to {intent['recipient']}: {intent.get('memo','')}",
            "format_instructions": components["judge_parser"].get_format_instructions(),
        })
        judgments.append({**verdict.model_dump(), "policy_context": policy_context})
    results["stages"]["judgments"] = judgments

    payment_results = []
    for intent in intents:
        req = SpendRequest(
            agent_id="pipeline",
            recipient=intent["recipient"],
            amount=intent["amount"],
            memo=intent.get("memo", ""),
        )
        result = guardrail.authorize(req)
        payment_results.append({**intent, **result})
    results["stages"]["payments"] = payment_results

    summary_prompt = f"""Summarize this treasury operation.

Request: {user_input}
Intents: {json.dumps(intents)}
Judgments: {json.dumps(judgments)}
Guardrail: {json.dumps(payment_results)}

Be direct. Note denials and approvals."""
    summary = components["llm"].invoke([HumanMessage(content=summary_prompt)]).content
    results["stages"]["summary"] = summary

    return results
