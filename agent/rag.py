from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

POLICY_DOCS = [
    "Software subscriptions under $50 are auto-approved if the vendor is allowlisted.",
    "Cloud infrastructure (AWS, GCP, Azure) is always pre-approved.",
    "Payments over $30 require finance team approval.",
    "Any payment to an unknown vendor must go through security review.",
    "Reimbursements to employees require a memo with the business purpose.",
]


def build_retriever():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    store = InMemoryVectorStore.from_texts(POLICY_DOCS, embeddings)
    return store.as_retriever(search_kwargs={"k": 2})
