from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama.chat_models import ChatOllama
from ..utils import scrub_think
from ..config import LOOP_MAX


def verify_or_refine(llm: ChatOllama, state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("loop", 0) >= LOOP_MAX:
        return state

    q = state["question"]
    ctx = "\n\n".join(d.page_content for d in state["graded_docs"])[:6000]
    ans = state.get("draft", "")[:4000]
    sys = SystemMessage(content=(
        "Judge if the answer is fully grounded in the provided context and addresses the question. "
        "Reply STRICTLY with one token among: PASS / REFINE."
    ))

    sys = SystemMessage(content=(
        "Judge if the answer is fully grounded in the provided context and addresses the question. "
        "Reply STRICTLY with one token among: PASS / REFINE."
    ))

    res = llm.invoke([sys, HumanMessage(
        content=f"Question:\n{q}\n\nContext:\n{ctx}\n\nAnswer:\n{ans}")])
    verdict = scrub_think(res.content).strip().upper()

    if verdict.startswith("REFINE"):
        qsys = SystemMessage(
            content="Suggest 1–2 sharper search queries for the question. One per line.")
        qres = llm.invoke([qsys, HumanMessage(content=q)])
        new_qs = [l.strip("- ").strip()
                  for l in scrub_think(qres.content).splitlines() if l.strip()]
        return {**state, "queries": [q] + new_qs[:2], "loop": state.get("loop", 0) + 1}

    return state
