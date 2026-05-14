"""测试写入命令"""
import sys
from pathlib import Path
from datetime import date, timedelta

# 添加项目路径
root_dir = Path(__file__).parent.parent / "Rogers"
sys.path.insert(0, str(root_dir))

import asyncio
import httpx


def _extract_text(content) -> str:
    """从 ToolResponse 的 content 中提取文本"""
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif "text" in block:
                    parts.append(str(block["text"]))
            elif hasattr(block, "text"):
                parts.append(str(block.text))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    return str(content)


async def test_write_commands():
    # 1. 先登录获取 token
    print("=== 步骤 1: 登录获取 token ===")
    login_resp = httpx.post(
        "http://localhost:8000/api/auth/login",
        json={"email": "user@test.com", "password": "password123"}
    )
    login_data = login_resp.json()
    token = login_data["data"]["token"]
    print(f"获取 token 成功: {token[:20]}...")

    # 2. 导入并测试工具
    print("\n=== 步骤 2: 测试写入命令 ===")
    from src.agents.harness.tools.basic_tools.fitme_shell_command import execute_fitme_command

    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # 测试写入命令
    test_cases = [
        # 健康指标
        f'create-health-metric --weight 68.5 --height 175 --body-fat 18.5',
        # 训练计划
        f'create-training-plan --plan-name "晨跑" --plan-type cardio --scheduled-date {tomorrow} --estimated-duration 30',
        # 饮食记录
        f'create-diet-meal --meal-type breakfast --meal-name "全麦面包+牛奶" --calories 350 --protein 15 --carbs 50 --fat 8',
    ]

    for cmd in test_cases:
        print(f"\n{'='*60}")
        print(f"测试命令: {cmd}")
        print(f"{'='*60}")
        try:
            resp = await execute_fitme_command(cmd, auth_token=token)
            text = _extract_text(resp.content)
            print(text)
        except Exception as e:
            print(f"执行异常: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_write_commands())
