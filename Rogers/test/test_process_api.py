#!/usr/bin/env python3
"""测试 /process 接口的脚本"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def login(email: str = "user@test.com", password: str = "password123"):
    """登录获取 token"""
    print(f"🔐 登录中: {email}")
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data["data"]["token"]
        print(f"✅ 登录成功!")
        return token
    else:
        print(f"❌ 登录失败: {resp.status_code}")
        print(resp.text)
        return None

def set_api_key(token: str, api_key: str):
    """设置 API Key"""
    print("🔑 设置 API Key...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/agent/config/api-key",
                       json={"api_key": api_key},
                       headers=headers)
    if resp.status_code == 200:
        print("✅ API Key 设置成功!")
        return True
    else:
        print(f"❌ API Key 设置失败: {resp.status_code}")
        print(resp.text)
        return False

def create_session(token: str, name: str = "测试会话"):
    """创建会话"""
    import uuid
    session_id = str(uuid.uuid4())
    print("🆕 创建会话...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/api/agent/sessions",
                       json={
                           "id": session_id,
                           "name": name
                       },
                       headers=headers)
    if resp.status_code == 200:
        print(f"✅ 会话创建成功: {session_id}")
        return session_id
    else:
        print(f"❌ 会话创建失败: {resp.status_code}")
        print(resp.text)
        return None

def test_process(token: str, session_id: str, message: str):
    """测试 /process 接口"""
    print(f"\n💬 发送消息: {message}")
    headers = {"Authorization": f"Bearer {token}"}

    # AgentScope 的 /process 接口正确格式 (来自 swagger)
    data = {
        "input": [
            {
                "content": [
                    {
                        "text": message,
                        "type": "text"
                    }
                ],
                "role": "user",
                "type": "message"
            }
        ],
        "session_id": session_id
    }

    print("📤 请求数据:", json.dumps(data, ensure_ascii=False, indent=2))

    # 使用流式请求
    with requests.post(f"{BASE_URL}/process",
                      json=data,
                      headers=headers,
                      stream=True) as resp:
        if resp.status_code == 200:
            print("✅ 请求成功!")
            print("\n" + "="*50)
            print("📨 流式响应:")
            print("="*50 + "\n")

            buffer = ""
            for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    buffer += chunk
                    # 尝试按行解析
                    lines = buffer.split("\n")
                    buffer = lines.pop()

                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                if line.startswith("data: "):
                                    # SSE 格式
                                    data_str = line[6:]
                                    if data_str == "[DONE]":
                                        print("\n✅ 完成!")
                                        continue
                                    msg = json.loads(data_str)
                                    print(f"📨 {json.dumps(msg, ensure_ascii=False, indent=2)}")
                                else:
                                    # 普通 JSON
                                    msg = json.loads(line)
                                    print(f"📨 {json.dumps(msg, ensure_ascii=False, indent=2)}")
                            except json.JSONDecodeError:
                                print(f"📝 {line}")
        else:
            print(f"❌ 请求失败: {resp.status_code}")
            print(resp.text)

def delete_session(token: str, session_id: str):
    """删除会话"""
    print(f"\n🗑️ 删除会话: {session_id}")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.delete(f"{BASE_URL}/api/agent/sessions/{session_id}", headers=headers)
    if resp.status_code == 200:
        print("✅ 会话删除成功!")
        return True
    else:
        print(f"❌ 会话删除失败: {resp.status_code}")
        print(resp.text)
        return False

if __name__ == "__main__":
    print("="*50)
    print("🧪 FitAgent /process 接口测试")
    print("="*50)

    # 配置email: str = "user@test.com", password: str = "password123"
    TEST_EMAIL = "user@test.com"
    TEST_PASSWORD = "password123"
    YOUR_API_KEY = input("请输入你的 DashScope API Key: ").strip()
    TEST_MESSAGE = input("请输入测试消息 (默认: hi，你是谁): ").strip()
    if not TEST_MESSAGE:
        TEST_MESSAGE = "hi，你是谁"

    # 执行测试
    print()
    token = login(TEST_EMAIL, TEST_PASSWORD)
    if not token:
        print("\n💡 提示: 如果没有测试账号,请先注册一个或检查账号密码")
        exit(1)

    if not set_api_key(token, YOUR_API_KEY):
        exit(1)

    session_id = create_session(token, "API测试会话")
    if not session_id:
        exit(1)

    # 等待一下确保会话创建完成
    time.sleep(1)

    test_process(token, session_id, TEST_MESSAGE)

    # 测试完成后删除会话
    delete_session(token, session_id)
