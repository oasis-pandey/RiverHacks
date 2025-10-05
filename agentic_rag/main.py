from .graph import GraphApp


def run_cli():
    app = GraphApp()
    print("Agentic RAG ready. Ask a question about your ingested corpus.\n")
    try:
        while True:
            q = input("Q> ").strip()
            if not q or q.lower() in {"exit", "quit"}:
                break
            state = app.invoke(q, thread_id="cli")
            print("\n=== ANSWER ===\n")
            print(state.get("draft", "(no answer)"))
            print("\n============\n")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_cli()
