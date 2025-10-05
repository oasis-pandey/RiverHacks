# agentic_rag/graph.py
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from .retrievers.supabase_ann import SupabaseANNRetriever
from .config import (
    EMBED_MODEL, GEN_MODEL, STOP_TOKENS, TOP_K,
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_QUERY, RP_PATH,
)
from .indexing import ensure_index
from .stores import open_vectorstore, build_bm25_from_store

from .nodes.plan import plan
from .nodes.expand import expand_queries
from .nodes.retrieve import retrieve
from .nodes.grade import grade_docs
from .nodes.generate import generate
from .nodes.verify import verify_or_refine


class GraphApp:
    """
    Clean Agentic RAG graph:
      - Embeddings: Gemini
      - Generation: Gemini
      - Retrieval: Supabase ANN (RP 3072->1024) and optional BM25 from Chroma
      - Planner -> Query Expansion -> Retrieve -> Grade -> Generate -> Verify (loop)
    """

    def __init__(
        self,
        # only set True if you want to (re)build local Chroma index
        build_index: bool = False,
        use_supabase: bool = True,   # enable ANN over pgvector (recommended)
        use_chroma: bool = False,    # keep Chroma around for BM25 if you want hybrid
    ):
        # 1) Models
        self.embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
        self.llm = ChatGoogleGenerativeAI(
            model=GEN_MODEL, temperature=0, stop=STOP_TOKENS)

        # 2) Retrieval backends
        # 2a) Supabase ANN (preferred)
        self.supa: Optional[SupabaseANNRetriever] = None
        if use_supabase:
            assert SUPABASE_URL and SUPABASE_KEY and RP_PATH, \
                "Missing Supabase env vars (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY or ANON / RP_PATH)."
            self.supa = SupabaseANNRetriever(
                url=SUPABASE_URL,
                key=SUPABASE_KEY,
                rpc_name=SUPABASE_QUERY,
                rp_path=RP_PATH,
                embedder=self.embeddings,
                k=TOP_K,
                probes=20,
            )

        # 2b) Optional Chroma & BM25 (for hybrid with lexical)
        self.vs = None
        self.bm25 = None
        if use_chroma:
            if build_index:
                # Build/refresh local Chroma index once (fingerprint-aware)
                ensure_index(self.embeddings)
            # Open existing Chroma store
            self.vs = open_vectorstore(self.embeddings)
            # Build BM25 from store docs (or return None if there are no docs)
            self.bm25 = build_bm25_from_store(self.vs)

        # Vector source to hand into the retrieve node (Supabase first, else Chroma)
        self._vec_source = self.supa if self.supa is not None else self.vs

        # 3) Graph skeleton
        self.workflow = StateGraph(dict)

        # 4) Nodes
        self.workflow.add_node("plan", lambda s: plan(self.llm, s))
        self.workflow.add_node("expand", lambda s: expand_queries(self.llm, s))
        self.workflow.add_node("retrieve", lambda s: retrieve(
            s, self._vec_source, self.bm25))
        self.workflow.add_node("grade", lambda s: grade_docs(self.llm, s))
        self.workflow.add_node("generate", lambda s: generate(self.llm, s))
        self.workflow.add_node(
            "verify", lambda s: verify_or_refine(self.llm, s))

        # 5) Edges
        self.workflow.add_edge(START, "plan")
        self.workflow.add_edge("plan", "expand")
        self.workflow.add_edge("expand", "retrieve")
        self.workflow.add_edge("retrieve", "grade")
        self.workflow.add_edge("grade", "generate")
        self.workflow.add_edge("generate", "verify")

        # 6) Loop routing after verification
        def route_after_verify(state: Dict[str, Any]):
            if state.get("loop", 0) and state.get("queries"):
                return "retrieve"
            return END

        self.workflow.add_conditional_edges(
            "verify",
            route_after_verify,
            {"retrieve": "retrieve", END: END},
        )

        # 7) Compile
        self.app = self.workflow.compile(checkpointer=MemorySaver())

    def invoke(self, question: str, thread_id: str = "api") -> Dict[str, Any]:
        """Run a single RAG turn."""
        init = {
            "question": question,
            "messages": [],
            "queries": [],
            "docs": [],
            "graded_docs": [],
            "draft": "",
            "loop": 0,
        }
        return self.app.invoke(init, config={"configurable": {"thread_id": thread_id}})
