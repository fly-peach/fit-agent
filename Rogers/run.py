"""Launch script"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file before anything else
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        port=8000,
        reload=True,
    )
