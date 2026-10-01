from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class PaymentIntent(BaseModel):
    recipient: str = Field(description="Merchant domain or person name")
    amount: float = Field(description="Dollar amount")
    memo: str = Field(description="Reason for payment")


class PaymentIntentList(BaseModel):
    payments: list[PaymentIntent] = Field(description="List of payments")


class JudgeVerdict(BaseModel):
    safety_score: int = Field(description="0-10 safety score")
    reasoning: str = Field(description="Why this score")
    flag: bool = Field(description="True if human review needed")


def build_llm_components(model_name: str = "qwen3:0.6b"):
    llm = ChatOllama(model=model_name, temperature=0)

    extraction_parser = PydanticOutputParser(pydantic_object=PaymentIntentList)
    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system", "Extract ALL payment intents from the user text. "
                   "If none, return an empty list.\n{format_instructions}"),
        ("human", "{user_input}")
    ])
    extraction_chain = extraction_prompt | llm | extraction_parser

    judge_parser = PydanticOutputParser(pydantic_object=JudgeVerdict)
    judge_prompt = ChatPromptTemplate.from_messages([
        ("system", "Score this payment safety 0-10.\n{format_instructions}"),
        ("human", "Payment: {payment}")
    ])
    judge_chain = judge_prompt | llm | judge_parser

    return {
        "llm": llm,
        "extraction_chain": extraction_chain,
        "extraction_parser": extraction_parser,
        "judge_chain": judge_chain,
        "judge_parser": judge_parser,
    }
