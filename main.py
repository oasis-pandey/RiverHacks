from typing import Literal
import os
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, MessagesState

from langchain_ollama.chat_models import ChatOllama
from langchain_ollama import OllamaEmbeddings


# ---------- Config ----------
# ör: nomic-embed-text / snowflake-arctic-embed / mxbai-embed-large
EMBED_MODEL = "mxbai-embed-large:latest"
PERSIST_DIR = "./chroma_python_docs"
COLLECTION = "python_docs"
JSON_PATH = "test.json"                    # tek JSON dosyan


# ---------- Helper: load JSON -> Documents (no JSONLoader) ----------
def load_docs_from_json(path: str) -> list[Document]:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)

    row = d.get("row", {})
    scr = d.get("scrape", {})

    # BOM'lu Title anahtarı için güvenli erişim
    title = row.get("\ufeffTitle") or row.get("Title", "")
    link = row.get("Link", "")

    text_blocks = [
        title,
        link,
        scr.get("title", ""),
        scr.get("abstract", ""),
        scr.get("full_text", ""),
    ]
    page_content = "\n\n".join([t for t in text_blocks if t])

    doc = Document(
        page_content=page_content,
        metadata={
            "url": scr.get("url"),
            "doi": scr.get("doi"),
            "source": os.path.basename(path),
            "title": title or scr.get("title", ""),
        },
    )
    return [doc]


# ---------- Build / Open Vectorstore ----------
embeddings = OllamaEmbeddings(model=EMBED_MODEL)


def ensure_index():
    """İndeks yoksa JSON'u yükleyip Chroma'ya yazar; varsa pas geçer."""
    needs_build = (not os.path.exists(PERSIST_DIR)) or (
        not os.listdir(PERSIST_DIR))
    if needs_build:
        if not os.path.exists(JSON_PATH):
            raise FileNotFoundError(f"JSON yok: {JSON_PATH}")

        docs = load_docs_from_json(JSON_PATH)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=50)
        chunks = splitter.split_documents(docs)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            collection_name=COLLECTION,
            embedding=embeddings,
            persist_directory=PERSIST_DIR,
        )
        vectorstore.persist()


# ilk çalıştırmada indeks oluştur
ensure_index()

# Var olan (veya yeni) indeksi aç
vectorstore = Chroma(
    collection_name=COLLECTION,
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})


# ---------- Model (no tools) ----------
# <think> sızıntısını engellemek için stop token ekledik; ekstra emniyet için post-process de yapıyoruz.
model = ChatOllama(
    model="deepseek-r1:7b",
    temperature=0,
    model_kwargs={"stop": ["</think>"]},
)


# ---------- Graph node ----------
def call_model(state: MessagesState):
    messages = state["messages"]

    # Son kullanıcı mesajını bul
    user_msg = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            user_msg = m.content
            break

    # Basit RAG: kullanıcı sorusuna göre bağlam getir
    ctx_docs = retriever.invoke(user_msg)
    context_text = "\n\n".join(d.page_content for d in ctx_docs)

    # Bağlam boşsa sertçe reddet
    if not context_text.strip():
        return {
            "messages": [
                HumanMessage(
                    content=(
                        "I couldn't find enough information in the indexed documents. "
                        "Try a more specific query about the ingested paper, e.g., "
                        "\"What were the main physiological systems studied in the Bion-M 1 mission?\""
                    )
                )
            ]
        }

    # Sadece bağlamdan cevap ver, yetersizse reddet; CoT istemiyoruz
    system = SystemMessage(
        content=(
            "You are a STRICT RAG assistant.\n"
            "- Use ONLY the Retrieved Context below to answer.\n"
            '- If the context is insufficient or unrelated, reply exactly: '
            '"I couldn\'t find enough information in the indexed documents." '
            "and suggest 1-2 better search queries.\n"
            "- Do NOT include chain-of-thought or <think> sections.\n\n"
            f"### Retrieved Context ###\n{context_text}"
        )
    )

    new_messages = [system] + messages
    response = model.invoke(new_messages)

    # Emniyet: kalan <think> sızıntısını temizle
    clean = re.sub(r"<think>.*?</think>\s*", "",
                   response.content, flags=re.DOTALL)
    return {"messages": [HumanMessage(content=clean)]}


# ---------- Graph ----------
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)


# ---------- Run ----------
if __name__ == "__main__":
    # Gerçek bir RAG testi için JSON içeriğine dair bir soru sorman en sağlıklısı
    final_state = app.invoke(
        {"messages": [HumanMessage(
            content="Bion-M 1 görevinde erkek farelerin seçilme nedeni neydi?")]},
        config={"configurable": {"thread_id": 42}},
    )
    print(final_state["messages"][-1].content)
