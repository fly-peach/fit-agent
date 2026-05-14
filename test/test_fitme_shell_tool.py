"""测试优化后的 fitme_shell_command 工具"""
import sys
from pathlib import Path

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


async def test_tool():
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
    print("\n=== 步骤 2: 测试 fitme_shell_command 工具 ===")
    from src.agents.harness.tools.basic_tools.fitme_shell_command import execute_fitme_command

    # 测试各个子命令（只读的先测）
    test_cases = [
        # 用户相关
        "get-user-profile",
        "get-user-settings",
        # 健康相关
        "get-health-metrics",
        "get-health-summary",
        "get-health-history",
        # 训练相关
        "get-training-today",
        "get-training-weekly",
        "get-training-stats",
        "get-training-recommendations",
        # 饮食相关
        "get-diet-today",
        "get-diet-stats",
        "get-diet-recommendations",
        "search-foods --keyword 鸡蛋",
        # 综合
        "get-full-overview",
    ]

    all_passed = True
    for cmd in test_cases:
        print(f"\n{'='*60}")
        print(f"测试命令: {cmd}")
        print(f"{'='*60}")
        try:
            resp = await execute_fitme_command(cmd, auth_token=token)
            # 提取并打印结果
            text = _extract_text(resp.content)
            print(text)
            # 简单判断是否成功
            if "错误" in text or "失败" in text or "error" in text.lower():
                print("\n[!] 命令执行似乎有问题")
                all_passed = False
            else:
                print("\n[OK] 命令执行成功")
        except Exception as e:
            print(f"\n[ERROR] 执行异常: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("[OK] 所有测试通过！")
    else:
        print("[!] 部分测试有问题")


if __name__ == "__main__":
    asyncio.run(test_tool())
