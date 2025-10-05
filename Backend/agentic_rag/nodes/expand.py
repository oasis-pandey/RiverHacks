from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama.chat_models import ChatOllama
from typing import Dict, Any
from ..config import HYDE_EXPS
from ..utils import scrub_think


def expand_queries(llm: ChatOllama, state: Dict[str, Any]) -> Dict[str, Any]:
    q = state["question"]
    sys = SystemMessage(content=(
        "Expand the user question into short, focused search queries and/or a brief HyDE-style note. "
        f"Generate up to {HYDE_EXPS} alternatives; one per line."
    ))
    res = llm.invoke([sys, HumanMessage(content=q)])
    lines = [l.strip("- ").strip()
             for l in scrub_think(res.content).splitlines() if l.strip()]
    queries = [q] + lines[:HYDE_EXPS]
    return {**state, "queries": queries}
