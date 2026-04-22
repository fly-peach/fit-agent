from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import User  # noqa: F401
from app.db.session import Base, engine

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST_DIR = PROJECT_ROOT / "webpage"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS_DIR)), name="assets")


def _ensure_phase13_schema() -> None:
    inspector = inspect(engine)
    with engine.begin() as conn:
        # 1) 新增表（若不存在）
        if not inspector.has_table("agent_offloads"):
            conn.execute(
                text(
                    """
                    CREATE TABLE agent_offloads (
                        id VARCHAR(64) PRIMARY KEY,
                        session_id VARCHAR(64) NOT NULL,
                        user_id INTEGER NOT NULL,
                        message_id INTEGER,
                        content_type VARCHAR(32) NOT NULL,
                        content TEXT NOT NULL,
                        compressed_summary TEXT,
                        created_at DATETIME NOT NULL,
                        loaded_at DATETIME,
                        load_count INTEGER NOT NULL DEFAULT 0
                    )
                    """
                )
            )
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_offloads_session_id ON agent_offloads (session_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_offloads_user_id ON agent_offloads (user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_offloads_message_id ON agent_offloads (message_id)"))

        if not inspector.has_table("agent_compression_events"):
            conn.execute(
                text(
                    """
                    CREATE TABLE agent_compression_events (
                        id INTEGER PRIMARY KEY,
                        session_id VARCHAR(64) NOT NULL,
                        user_id INTEGER NOT NULL,
                        run_id VARCHAR(64) NOT NULL,
                        strategy_level INTEGER NOT NULL,
                        strategy_name VARCHAR(64) NOT NULL,
                        messages_before INTEGER NOT NULL,
                        messages_after INTEGER NOT NULL,
                        tokens_before INTEGER NOT NULL,
                        tokens_after INTEGER NOT NULL,
                        compression_ratio FLOAT NOT NULL,
                        affected_message_ids TEXT,
                        created_at DATETIME NOT NULL
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_agent_compression_events_session_id ON agent_compression_events (session_id)")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_agent_compression_events_user_id ON agent_compression_events (user_id)")
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_agent_compression_events_run_id ON agent_compression_events (run_id)")
            )

        # 2) 旧表补列（兼容已有数据库）
        if inspector.has_table("agent_messages"):
            cols = {c["name"] for c in inspector.get_columns("agent_messages")}
            if "is_compressed" not in cols:
                conn.execute(text("ALTER TABLE agent_messages ADD COLUMN is_compressed BOOLEAN NOT NULL DEFAULT 0"))
            if "compression_strategy" not in cols:
                conn.execute(text("ALTER TABLE agent_messages ADD COLUMN compression_strategy VARCHAR(64)"))
            if "offload_id" not in cols:
                conn.execute(text("ALTER TABLE agent_messages ADD COLUMN offload_id VARCHAR(64)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_agent_messages_offload_id ON agent_messages (offload_id)"))
            if "compressed_summary" not in cols:
                conn.execute(text("ALTER TABLE agent_messages ADD COLUMN compressed_summary TEXT"))


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_phase13_schema()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def serve_index():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="前端静态资源不存在，请先执行前端构建与复制。")
    return FileResponse(index_file)


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    # 避免吞掉 API 路由，未命中 API 时才由前端路由接管
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")

    candidate = FRONTEND_DIST_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="前端静态资源不存在，请先执行前端构建与复制。")
