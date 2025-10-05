from typing import Dict, Any, List
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama.chat_models import ChatOllama
from ..utils import scrub_think


def grade_docs(llm: ChatOllama, state: Dict[str, Any]) -> Dict[str, Any]:
    q = state["question"]
    graded: List[Document] = []
    grader_sys = SystemMessage(content=(
        "You rate if a passage is RELEVANT to the question. Reply only 'YES' or 'NO'."
    ))

    for d in state["docs"]:
        res = llm.invoke([grader_sys, HumanMessage(
            content=f"Question:\n{q}\n\nPassage:\n{d.page_content[:1200]}")])
        if scrub_think(res.content).strip().upper().startswith("Y"):
            graded.append(d)
        if not graded:
            graded = state["docs"][:2]
            return {**state, "graded_docs": graded}
