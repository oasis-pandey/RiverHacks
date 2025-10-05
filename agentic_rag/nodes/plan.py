from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any
from ..utils import scrub_think


def plan(llm: ChatOllama, state: Dict[str, Any]) -> Dict[str, Any]:
    q = state["question"]
    sys = SystemMessage(content=(
        "Classify if this question should be answerable from the ingested corpus. "
        "Reply 'CORPUS' or 'OUTSIDE'. No extra text."
    ))
    res = llm.invoke([sys, HumanMessage(content=q)])
    _ = scrub_think(res.content).strip().upper()  # reserved for routing
    return {**state, "queries": [q]}
