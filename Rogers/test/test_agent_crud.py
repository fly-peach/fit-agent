#!/usr/bin/env python3
"""测试 Agent 工具调用审批 + 用户记忆数据库变更

流程:
1. 登录 + 设置 API Key
2. 发送 prompt 让 Agent 调用 record_user_fact 写入个性数据
3. 审批拦截 → 在 SSE 流中检测到 approval_id → 手动批准
4. 查看 Agent 最终输出的确认文本
5. 查询 user_memory_profile 表，展示刚写入的内部数据
6. 删除测试记录 + 会话
"""
import sys
import os
import json
import uuid
import requests

# 添加项目根到 sys.path，以便直接导入 user_profile 查询数据库
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents.harness.memory.user_profile import get_user_facts, delete_user_fact

BASE_URL = "http://localhost:8000"
TEST_KEY = "test_personality"
AUTO_APPROVE_FIELD = "autoApproveDbWrite"


def login(email: str = "user@test.com", password: str = "password123"):
    print(f"🔐 登录中: {email}")
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email, "password": password
    })
    if resp.status_code != 200:
        print(f"❌ 登录失败: {resp.status_code} {resp.text}")
        return None
    token = resp.json()["data"]["token"]
    print("✅ 登录成功")
    return token


def set_api_key(token: str, api_key: str):
    print("🔑 设置 API Key...")
    resp = requests.put(
        f"{BASE_URL}/api/agent/api-key",
        json={"api_key": api_key},
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code == 200:
        print("✅ API Key 设置成功")
        return True
    print(f"❌ API Key 设置失败: {resp.status_code} {resp.text}")
    return False


def run_agent_pipeline(token: str, session_id: str, message: str) -> str | None:
    """发送消息给 Agent，在流中检测审批并等待用户手动批准，返回完整响应文本"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "input": [{
            "content": [{"text": message, "type": "text"}],
            "role": "user",
            "type": "message",
        }],
        "session_id": session_id,
    }

    approval_id = None
    text_parts = []
    print(f"\n💬 发送: {message}")
    print("=" * 60)

    with requests.post(
        f"{BASE_URL}/process", json=data, headers=headers, stream=True
    ) as resp:
        if resp.status_code != 200:
            print(f"❌ 请求失败: {resp.status_code} {resp.text}")
            return None

        buffer = ""
        for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
            if not chunk:
                continue
            buffer += chunk
            lines = buffer.split("\n")
            buffer = lines.pop()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 统一去掉 data: 前缀
                raw = line[6:] if line.startswith("data: ") else line
                if raw == "[DONE]":
                    continue
                try:
                    msg = json.loads(raw)
                    print(f"📨 {msg}")

                    # 检测审批通知 - 检查 metadata 字段
                    metadata = msg.get("metadata", {})
                    if isinstance(metadata, dict):
                        tool_meta = metadata.get("tool_approval")
                        if tool_meta and not approval_id:
                            approval_id = tool_meta["approval_id"]
                            tool_name = tool_meta["tool_name"]
                            tool_args = tool_meta.get("tool_args_display", "")

                            print(f"\n{'='*60}")
                            print(f"🔔 【需要审批】工具: {tool_name}")
                            if tool_args:
                                print(f"   参数: {tool_args}")
                            print(f"\n请选择:")
                            print(f"   y - 批准执行此工具")
                            print(f"   n - 拒绝执行此工具")

                            # 等待用户输入
                            while True:
                                choice = input("\n请输入你的选择 (y/n): ").strip().lower()
                                if choice in ['y', 'n']:
                                    break
                                print("无效输入，请输入 y 或 n")

                            if choice == 'y':
                                # 批准
                                ar = requests.post(
                                    f"{BASE_URL}/api/agent/approval/{approval_id}/approve",
                                    headers=headers,
                                )
                                print(f"\n✅ 已批准! 审批结果: {ar.json()}")
                            else:
                                # 拒绝
                                ar = requests.post(
                                    f"{BASE_URL}/api/agent/approval/{approval_id}/reject",
                                    headers=headers,
                                )
                                print(f"\n❌ 已拒绝! 审批结果: {ar.json()}")

                            print(f"{'='*60}\n")

                    # 收集文本输出 - 新格式适配
                    obj_type = msg.get("object", "")
                    if obj_type == "content":
                        # 新格式：object=content 时有 text 字段
                        text = msg.get("text", "")
                        if text:
                            text_parts.append(text)
                    elif obj_type == "message":
                        # 旧格式兼容
                        content = msg.get("content")
                        if content:
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        text_parts.append(c.get("text", ""))
                            elif isinstance(content, str):
                                text_parts.append(content)
                except json.JSONDecodeError:
                    print(f"📝 {line}")

    print("=" * 60)
    return "".join(text_parts)


def set_auto_approve(token: str, enabled: bool):
    """设置自动审批开关"""
    resp = requests.put(
        f"{BASE_URL}/api/user/settings",
        json={AUTO_APPROVE_FIELD: enabled},
        headers={"Authorization": f"Bearer {token}"},
    )
    ok = resp.status_code == 200
    print(f"{'✅' if ok else '❌'} 自动审批 → {'开启' if enabled else '关闭'}"
          f"{'' if ok else f' ({resp.status_code})'}")


def show_memory_data(user_id: int, label: str):
    """查询 user_memory_profile 表并打印"""
    facts = get_user_facts(user_id, category="personality")
    filtered = [f for f in facts if f["key"] == TEST_KEY]
    if filtered:
        print(f"\n📦 {label} — user_memory_profile 记录:")
        for f in filtered:
            print(f"   id={f['id']}  key={f['key']}  value={f['value']}  "
                  f"source={f['source']}  confidence={f['confidence']}")
    else:
        print(f"\n📭 {label} — 无 {TEST_KEY} 记录")


def delete_test_data(user_id: int, session_id: str, token: str):
    """清理测试数据"""
    # 1. 软删除 memory profile 记录
    deleted = delete_user_fact(user_id, TEST_KEY)
    print(f"🗑️  软删除 memory key={TEST_KEY}: {'成功' if deleted else '未找到'}")

    # 2. 删除会话
    resp = requests.delete(
        f"{BASE_URL}/api/agent/pipeline/sessions/{session_id}",
        params={"user_id": user_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"🗑️  删除会话: {resp.json()}")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 测试: Agent 写工具调用审批 + 记忆数据库变更")
    print("=" * 60)

    user_id = 1
    TEST_EMAIL = "user@test.com"
    TEST_PASSWORD = "password123"
    YOUR_API_KEY = input("请输入 DashScope API Key: ").strip()

    # ── 1. 登录 & 准备 ──
    token = login(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        sys.exit(1)
    if not set_api_key(token, YOUR_API_KEY):
        sys.exit(1)

    session_id = str(uuid.uuid4())
    print(f"🆕 会话: {session_id}")

    # 关闭自动审批，启用手动审批流程
    set_auto_approve(token, False)

    # 清理之前残留的测试数据
    delete_user_fact(user_id, TEST_KEY)

    # ── 2. 查看写入前数据库状态 ──
    show_memory_data(user_id, "写入前")

    # ── 3. 发送 prompt 让 Agent 调用 record_user_fact ──
    prompt = (
        "你好，我是新用户。请使用 record_user_fact 工具记录我的性格特征。\n"
        "参数如下：\n"
        "  category: personality\n"
        "  key: test_personality\n"
        "  value: 外向开朗，喜欢社交，热爱健身，乐于尝试新事物\n"
        "  user_id: 1\n"
        "请调用该工具并将结果告诉我。"
    )
    response_text = run_agent_pipeline(token, session_id, prompt)

    if response_text:
        print(f"\n📝 Agent 最终回复:\n{response_text}")

    # ── 4. 查看写入后的数据库状态 ──
    show_memory_data(user_id, "写入后")

    # ── 5. 清理 ──
    delete_test_data(user_id, session_id, token)

    # ── 6. 最终验证 ──
    show_memory_data(user_id, "清理后")
    print("\n✅ 测试完成!")
