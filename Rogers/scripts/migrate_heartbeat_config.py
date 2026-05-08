"""迁移存量用户的 agent.json，补充心跳配置字段。

用法: python scripts/migrate_heartbeat_config.py

该脚本会扫描所有用户工作区中的 agent.json，为缺少 heartbeat 字段的
配置文件补充默认心跳设置（默认关闭）。
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from dotenv import load_dotenv
load_dotenv(dotenv_path=_project_root / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("migrate_heartbeat")

DEFAULT_HEARTBEAT = {"enabled": False, "every": "6h", "target": "main"}


def _find_agent_json_files() -> list[Path]:
    files: list[Path] = []
    try:
        from src.fitme.utils.database import UserSessionLocal
        from src.fitme.crud.agent_config import get_all_agent_configs
        db = UserSessionLocal()
        try:
            configs = get_all_agent_configs(db)
            for cfg in configs:
                if cfg.local_working_dir:
                    p = Path(str(cfg.local_working_dir)) / "agent.json"
                    if p.exists():
                        files.append(p)
        finally:
            db.close()
    except Exception as e:
        logger.warning("Failed to load configs from DB: %s", e)

    home = Path(os.environ.get("FITAGENT_HOME", Path.home() / ".fitagent"))
    p = home / "agent.json"
    if p.exists() and p not in files:
        files.append(p)

    legacy_dir = _project_root / "data" / "agent_db" / "workspace" / "users"
    if legacy_dir.exists():
        for user_dir in legacy_dir.iterdir():
            p = user_dir / "agent.json"
            if p.exists() and p not in files:
                files.append(p)

    return files


def _migrate_file(filepath: Path) -> bool:
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Skipping invalid JSON: %s", filepath)
        return False
    if "heartbeat" in data:
        return False
    data["heartbeat"] = DEFAULT_HEARTBEAT
    try:
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        logger.info("Migrated: %s", filepath)
        return True
    except Exception as e:
        logger.error("Failed to write %s: %s", filepath, e)
        return False


def main() -> None:
    logger.info("Starting heartbeat config migration...")
    files = _find_agent_json_files()
    logger.info("Found %d agent.json files to check", len(files))
    migrated = skipped = 0
    for fp in files:
        if _migrate_file(fp):
            migrated += 1
        else:
            skipped += 1
    logger.info("Migration complete: %d migrated, %d skipped", migrated, skipped)


if __name__ == "__main__":
    main()
