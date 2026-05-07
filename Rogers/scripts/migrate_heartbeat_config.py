"""迁移脚本：为现有用户的工作区添加心跳 (heartbeat) 配置。

背景：
    心跳系统是参考 CoPaw 的提示词驱动心跳管理实现的。
    新用户通过 ``ensure_user_workspace()`` 创建时会自动获得完整配置，
    但已有用户的工作区中 ``agent.json`` 和 ``memory_config.json`` 可能缺少
    heartbeat 字段。

本脚本会遍历所有已有用户，为他们的工作区补全：
1. ``agent.json`` → 添加 ``heartbeat`` 节（默认禁用）
2. ``memory_config.json`` → 添加 ``heartbeat`` 节（默认禁用）
3. ``HEARTBEAT.md`` → 如果不存在则从模板复制

用法：
    cd rogers
    python scripts/migrate_heartbeat_config.py          # 扫描但不修改（dry-run）
    python scripts/migrate_heartbeat_config.py --apply   # 实际应用迁移
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# 确保能导入项目模块
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


DEFAULT_HEARTBEAT_CONFIG = {
    "enabled": False,
    "every": "6h",
    "target": "main",
    "active_hours": None,
}

DEFAULT_HEARTBEAT_IN_AGENT_JSON = {
    "enabled": False,
    "every": "6h",
    "target": "main",
}

HEARTBEAT_TEMPLATE_CONTENT = """# HEARTBEAT.md

# 保持此文件为空（或仅含注释）以跳过心跳 API 调用。
# 在下文添加需要 agent 定期检查的任务。

# 示例任务（取消注释使用）：
# 1. 检查最近 3 天的 memory/*.md，更新 MEMORY.md
# 2. 检查用户是否有未完成的训练计划
# 3. 回顾用户的健康指标趋势
"""


def find_all_user_dirs() -> list[Path]:
    """扫描所有可能的用户工作区目录。

    策略：
    1. 从数据库读取用户配置的 local_working_dir
    2. 使用默认目录 ~/.fitagent
    3. 检查旧版 workspace/users/{user_id} 目录
    """
    user_dirs: list[Path] = []
    seen: set[str] = set()

    def _add(p: Path) -> None:
        resolved = p.resolve()
        key = str(resolved).lower()
        if resolved.is_dir() and key not in seen:
            seen.add(key)
            user_dirs.append(resolved)

    # 方法1：从数据库读取
    try:
        from src.fitme.utils.database import UserSessionLocal
        from src.fitme.crud import agent_config as agent_crud

        db = UserSessionLocal()
        try:
            configs = agent_crud.get_all_agent_configs(db)
            for cfg in configs:
                raw = cfg.local_working_dir
                if raw and raw.strip():
                    _add(Path(str(raw).strip()))
        finally:
            db.close()
    except Exception as e:
        print(f"  [!] 从数据库读取失败: {e}")

    # 方法2：检查默认目录 ~/.fitagent
    _add(Path.home() / ".fitagent")

    # 方法3：检查旧版 workspace/users/{user_id} 目录
    old_users_dir = _PROJECT_ROOT / "data" / "agent_db" / "workspace" / "users"
    if old_users_dir.is_dir():
        for child in sorted(old_users_dir.iterdir()):
            if child.is_dir() and child.name.isdigit():
                _add(child)

    return user_dirs


def migrate_agent_json(user_dir: Path, apply: bool) -> list[str]:
    """补全 agent.json 的 heartbeat 字段。

    Args:
        user_dir: 用户工作区目录
        apply: 是否实际写入

    Returns:
        操作描述列表
    """
    reports: list[str] = []
    agent_json = user_dir / "agent.json"

    if not agent_json.exists():
        reports.append(f"  - agent.json 不存在，跳过")
        return reports

    try:
        data = json.loads(agent_json.read_text(encoding="utf-8"))

        if "heartbeat" in data and isinstance(data["heartbeat"], dict):
            reports.append(f"  ✓ agent.json 已有 heartbeat，跳过")
            return reports

        data["heartbeat"] = dict(DEFAULT_HEARTBEAT_IN_AGENT_JSON)
        reports.append(
            f"  {'✓' if apply else '→'} agent.json → 添加 heartbeat 配置"
        )

        if apply:
            agent_json.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
    except Exception as e:
        reports.append(f"  ✗ agent.json 处理失败: {e}")

    return reports


def migrate_memory_config_json(user_dir: Path, apply: bool) -> list[str]:
    """补全 memory_config.json 的 heartbeat 字段。"""
    reports: list[str] = []

    # 检查 workspace/memory_config.json 或直接放在 user_dir 中
    memory_config_paths = [
        user_dir / "memory_config.json",
        user_dir / "workspace" / "memory_config.json",
    ]

    for mcp in memory_config_paths:
        if not mcp.exists():
            continue

        try:
            data = json.loads(mcp.read_text(encoding="utf-8"))

            if "heartbeat" in data and isinstance(data["heartbeat"], dict):
                reports.append(
                    f"  ✓ {mcp.name} 已有 heartbeat，跳过"
                )
                return reports

            data["heartbeat"] = dict(DEFAULT_HEARTBEAT_CONFIG)
            reports.append(
                f"  {'✓' if apply else '→'} {mcp.name} → 添加 heartbeat 配置"
            )

            if apply:
                mcp.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            return reports
        except Exception as e:
            reports.append(f"  ✗ {mcp.name} 处理失败: {e}")

    reports.append(f"  - memory_config.json 不存在")
    return reports


def ensure_heartbeat_md(user_dir: Path, apply: bool) -> list[str]:
    """如果 HEARTBEAT.md 不存在则从模板复制。"""
    reports: list[str] = []
    hb_path = user_dir / "HEARTBEAT.md"

    if hb_path.exists():
        reports.append(f"  ✓ HEARTBEAT.md 已存在")
        return reports

    reports.append(
        f"  {'✓' if apply else '→'} HEARTBEAT.md → 创建默认模板"
    )

    if apply:
        hb_path.write_text(HEARTBEAT_TEMPLATE_CONTENT, encoding="utf-8")

    return reports


def main():
    parser = argparse.ArgumentParser(
        description="迁移现有用户工作区，补全心跳配置",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际应用迁移（默认 dry-run）",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  心跳配置迁移脚本")
    print(f"  模式: {'APPLY (实际写入)' if args.apply else 'DRY-RUN (仅扫描)'}")
    print("=" * 60)

    user_dirs = find_all_user_dirs()

    if not user_dirs:
        print("\n没有找到用户工作区。")
        return

    print(f"\n发现 {len(user_dirs)} 个工作区:\n")

    total_changes = 0
    for i, user_dir in enumerate(user_dirs, 1):
        print(f"[{i}/{len(user_dirs)}] {user_dir}")

        reports = []
        reports.extend(migrate_agent_json(user_dir, args.apply))
        reports.extend(migrate_memory_config_json(user_dir, args.apply))
        reports.extend(ensure_heartbeat_md(user_dir, args.apply))

        for r in reports:
            print(r)
        print()

        changes = sum(1 for r in reports if "→" in r)
        total_changes += changes

    print("=" * 60)
    if args.apply:
        print(f"  迁移完成！共处理 {total_changes} 个变更。")
        print(f"  后续：用户登录后即可在「记忆管理」页面配置心跳。")
    else:
        print(f"  Dry-Run 完成。检测到 {total_changes} 个待迁移项。")
        print(f"  执行 python scripts/migrate_heartbeat_config.py --apply 来应用。")
    print("=" * 60)


if __name__ == "__main__":
    main()
