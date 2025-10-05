# server/core/app.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.api.routes.health import router as health_router
from server.api.routes.rag import router as rag_router
from server.core.logging import quiet_third_party_logs
from server.api.routes.hybrid import router as hybrid_router


def create_app() -> FastAPI:
    load_dotenv()
    quiet_third_party_logs()  # silence grpc/absl

    # Read API base path & CORS from env
    api_root = os.getenv("API_ROOT_PATH", "/api/v1")

    allow_origins = os.getenv("ALLOW_ORIGINS", "*")
    if allow_origins.strip() == "*":
        origins = ["*"]
    else:
        origins = [o.strip() for o in allow_origins.split(",") if o.strip()]

    allow_methods = os.getenv("ALLOW_METHODS", "*")
    methods = ["*"] if allow_methods.strip() == "*" else [m.strip()
                                                          for m in allow_methods.split(",")]

    allow_headers = os.getenv("ALLOW_HEADERS", "*")
    headers = ["*"] if allow_headers.strip() == "*" else [h.strip()
                                                          for h in allow_headers.split(",")]

    allow_credentials = os.getenv(
        "ALLOW_CREDENTIALS", "true").lower() == "true"

    app = FastAPI(
        title="Agentic RAG API",
        version="0.1.0",
        root_path=api_root,   # e.g. /api/v1
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=methods,
        allow_headers=headers,
    )

    # Lazy import to avoid heavy deps on import
    from agentic_rag.graph import GraphApp
    app.state.graph = GraphApp(build_index=False)

    app.include_router(health_router)
    app.include_router(rag_router)
    app.include_router(hybrid_router)
    return app
