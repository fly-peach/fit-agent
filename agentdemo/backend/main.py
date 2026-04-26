# FastAPI app entry point for chat demo backend
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import uvicorn

from routers import chat
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Frontend dist directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
FRONTEND_DIST = FRONTEND_DIR  # 直接使用 frontend 目录

app = FastAPI(
    title="Chat Demo Backend",
    description="Simple chat backend with streaming SSE responses",
    version="0.1.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include chat router
app.include_router(chat.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Serve frontend static files
if FRONTEND_DIST.exists():
    # 尝试挂载 assets 目录（如果不存在则跳过）
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # 挂载整个前端目录用于静态文件
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/styles.css")
    async def serve_styles():
        return FileResponse(FRONTEND_DIST / "styles.css")

    @app.get("/app.js")
    async def serve_app_js():
        return FileResponse(FRONTEND_DIST / "app.js")

    @app.get("/favicon.svg")
    async def serve_favicon():
        return FileResponse(FRONTEND_DIST / "favicon.svg")

    @app.get("/favicon.ico")
    async def serve_favicon_ico():
        # 如果没有 favicon.ico，返回 204 No Content
        favicon_path = FRONTEND_DIST / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        from fastapi.responses import Response
        return Response(status_code=204)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=True,
    )