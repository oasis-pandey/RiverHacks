import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama.chat_models import ChatOllama
from ..utils import scrub_think, cite_block


def _normalize_sources(draft: str, cites: str) -> str:
    """
    Model her ne yazarsa yazsın (hatta boş 'Sources:' bile yazsa),
    mevcut 'Sources:' bloğunu at ve bizim 'cites' ile yeniden ekle.
    """
    parts = re.split(r"\n\s*Sources\s*:?\s*\n", draft,
                     maxsplit=1, flags=re.IGNORECASE)
    body = parts[0].rstrip()
    cites = cites or "- (no sources)"
    return body + "\n\nSources:\n" + cites


def generate(llm: ChatOllama, state: Dict[str, Any]) -> Dict[str, Any]:
    q = state["question"]

    # 1) Bağlam/kanıt yoksa: açıkça reddet + 1-2 öneri ver
    if not state.get("graded_docs"):
        suggestions = [s for s in state.get("queries", []) if s.strip()][:2]
        if not suggestions:
            suggestions = [
                "Ask about the ingested document's content (use specific keywords).",
                "Example: 'What were the main findings reported in the paper?'",
            ]
        draft = (
            "I couldn't find enough information in the indexed documents.\n"
            "Try one of these queries:\n- " + "\n- ".join(suggestions)
        )
        draft = _normalize_sources(draft, cites="- (no sources)")
        return {**state, "draft": draft}

    # 2) Bağlam var → cevabı üret
    ctx = "\n\n---\n\n".join(
        f"[{i+1}] {d.metadata.get('title') or '(untitled)'} "
        f"({d.metadata.get('url') or d.metadata.get('source')})\n{d.page_content}"
        for i, d in enumerate(state["graded_docs"])
    )
    sys = SystemMessage(content=(
        "You are a STRICT RAG assistant.\n"
        "- Answer ONLY using the context. If insufficient, say exactly:\n"
        "  \"I couldn't find enough information in the indexed documents.\" and suggest 1–2 improved queries.\n"
        "- No chain-of-thought. Be concise, precise, and cite.\n"
        "- End with a 'Sources:' list (bullet points).\n\n"
        f"### Context ###\n{ctx}"
    ))
    res = llm.invoke([sys, HumanMessage(content=q)])
    draft = scrub_think(res.content)

    # 3) Kaynak listesini daima biz sonlandırıyoruz (modelinkini override ediyoruz)
    cites = cite_block(state["graded_docs"]) or "- (no sources)"
    draft = _normalize_sources(draft, cites)
    return {**state, "draft": draft}
