# Simple chat agent using OpenAI-compatible API (DeepSeek)
"""Enhanced chat agent with streaming support, reasoning, and tool integration."""
import json
import uuid
import time
import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk

import config

logger = logging.getLogger(__name__)


# Global pending approvals storage
_pending_approvals: Dict[str, asyncio.Event] = {}
_approval_results: Dict[str, bool] = {}


def create_approval_request(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Create a new approval request and return its ID."""
    approval_id = f"approval_{uuid.uuid4().hex[:8]}"
    _pending_approvals[approval_id] = asyncio.Event()
    return approval_id


async def wait_for_approval(approval_id: str, timeout: float = 300.0) -> bool:
    """Wait for user approval. Returns True if approved, False otherwise."""
    if approval_id not in _pending_approvals:
        return False

    try:
        await asyncio.wait_for(_pending_approvals[approval_id].wait(), timeout=timeout)
        result = _approval_results.get(approval_id, False)
        return result
    except asyncio.TimeoutError:
        return False
    finally:
        # Cleanup
        if approval_id in _pending_approvals:
            del _pending_approvals[approval_id]
        if approval_id in _approval_results:
            del _approval_results[approval_id]


def submit_approval(approval_id: str, approved: bool) -> bool:
    """Submit user approval decision."""
    if approval_id not in _pending_approvals:
        return False

    _approval_results[approval_id] = approved
    _pending_approvals[approval_id].set()
    return True


@dataclass
class Tool:
    """Tool definition for function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: callable = field(default=None)


class ChatMessage:
    """Represents a chat message with content and optional reasoning."""

    def __init__(self, role: str, content: str, reasoning_content: Optional[str] = None,
                 tool_calls: Optional[List[Dict]] = None, tool_call_id: Optional[str] = None):
        self.role = role
        self.content = content
        self.reasoning_content = reasoning_content
        self.tool_calls = tool_calls
        self.tool_call_id = tool_call_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API-compatible dict."""
        msg = {"role": self.role, "content": self.content}
        if self.reasoning_content:
            msg["reasoning_content"] = self.reasoning_content
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        return msg


class SimpleChatAgent:
    """Enhanced chat agent with conversation memory, streaming, reasoning, and tool support."""

    def __init__(self, enable_reasoning: bool = False, enable_tools: bool = False, tools_require_approval: List[str] = None):
        self.client = AsyncOpenAI(
            api_key=config.API_KEY,
            base_url=config.BASE_URL,
        )
        self.messages: List[ChatMessage] = []
        self.system_prompt = "You are a helpful AI assistant."
        self.enable_reasoning = enable_reasoning
        self.enable_tools = enable_tools
        self.tools: Dict[str, Tool] = {}
        # 需要审批的工具列表，默认包含 python 相关工具
        self.tools_require_approval = tools_require_approval or ["execute_python", "execute_shell_command"]

        # Register default tools if enabled
        if enable_tools:
            self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools for the agent."""

        async def execute_python(code: str) -> str:
            """Execute Python code and return the result."""
            try:
                # Create a safe execution environment
                import io
                import sys
                stdout = io.StringIO()
                stderr = io.StringIO()

                exec_globals = {
                    "__builtins__": __builtins__,
                    "print": lambda *args, **kwargs: print(*args, file=stdout, **kwargs),
                }

                old_stdout, old_stderr = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = stdout, stderr

                try:
                    result = eval(code, exec_globals)
                    if result is not None:
                        output = str(result)
                    else:
                        output = stdout.getvalue()
                except SyntaxError:
                    exec(code, exec_globals)
                    output = stdout.getvalue()

                sys.stdout, sys.stderr = old_stdout, old_stderr

                error_output = stderr.getvalue()
                if error_output:
                    return f"Error: {error_output}"
                return output or "Code executed successfully (no output)"
            except Exception as e:
                return f"Error: {str(e)}"

        async def get_current_time() -> str:
            """Get current date and time."""
            from datetime import datetime
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        async def calculate(expression: str) -> str:
            """Calculate a mathematical expression."""
            try:
                allowed_chars = set("0123456789+-*/.() ")
                if not all(c in allowed_chars for c in expression):
                    return "Error: Invalid characters in expression"
                result = eval(expression, {"__builtins__": {}})
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        async def get_weather(location: str) -> str:
            """Get weather information for a location."""
            # 模拟天气数据
            import random
            from datetime import datetime
            weather_conditions = ["晴朗", "多云", "阴天", "小雨", "中雨", "雷阵雨"]
            condition = random.choice(weather_conditions)
            temperature = random.randint(15, 35)
            humidity = random.randint(40, 90)
            wind_speed = random.randint(0, 20)

            result = {
                "location": location,
                "weather": condition,
                "temperature": f"{temperature}°C",
                "humidity": f"{humidity}%",
                "wind_speed": f"{wind_speed} km/h",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        async def get_coordinates(address: str) -> str:
            """Get latitude and longitude for an address."""
            # 模拟经纬度数据（基于地址生成伪随机但一致的坐标）
            import hashlib
            hash_val = int(hashlib.md5(address.encode()).hexdigest(), 16)

            # 生成大致在中国的经纬度范围
            base_lat = 30.0 + (hash_val % 1000) / 1000 * 20  # 30-50度纬度
            base_lng = 100.0 + (hash_val % 2000) / 2000 * 30  # 100-130度经度

            # 添加小数部分
            lat = round(base_lat + (hash_val >> 10) % 100 / 10000, 6)
            lng = round(base_lng + (hash_val >> 20) % 100 / 10000, 6)

            result = {
                "address": address,
                "latitude": lat,
                "longitude": lng,
                "coordinate_system": "WGS84",
                "location_type": "模拟数据"
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        async def search_places(query: str, limit: int = 5) -> str:
            """Search for places by keyword."""
            # 模拟地点搜索结果
            mock_places = {
                "餐厅": ["老北京炸酱面", "海底捞火锅", "西贝莜面村", "必胜客", "麦当劳"],
                "酒店": ["希尔顿酒店", "如家快捷酒店", "汉庭酒店", "7天连锁酒店", "喜来登酒店"],
                "景点": ["故宫博物院", "长城", "颐和园", "天坛公园", "圆明园"],
                "商场": ["王府井百货", "西单大悦城", "三里屯太古里", "国贸商城", "朝阳大悦城"]
            }

            results = []
            for category, places in mock_places.items():
                if query in category or any(query in place for place in places):
                    for place in places[:limit]:
                        results.append({
                            "name": place,
                            "category": category,
                            "rating": round(3.5 + (hash(place) % 15) / 10, 1),
                            "price_level": "¥" * (1 + hash(place) % 4)
                        })

            if not results:
                results = [
                    {"name": f"{query}搜索结果1", "category": "其他", "rating": 4.2, "price_level": "¥¥"},
                    {"name": f"{query}搜索结果2", "category": "其他", "rating": 4.5, "price_level": "¥¥¥"}
                ]

            return json.dumps({
                "query": query,
                "total": len(results),
                "results": results[:limit]
            }, ensure_ascii=False, indent=2)

        async def translate_text(text: str, target_language: str = "en") -> str:
            """Translate text to target language."""
            # 模拟翻译结果
            translations = {
                "en": f"[Translated to English]: {text}",
                "zh": f"[翻译为中文]: {text}",
                "ja": f"[日本語に翻訳]: {text}",
                "fr": f"[Traduit en français]: {text}",
                "es": f"[Traducido al español]: {text}"
            }
            translated = translations.get(target_language, f"[Translated]: {text}")

            result = {
                "original_text": text,
                "translated_text": translated,
                "source_language": "auto",
                "target_language": target_language
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        async def get_news(category: str = "general", count: int = 3) -> str:
            """Get latest news by category."""
            # 模拟新闻数据
            news_data = {
                "general": [
                    {"title": "科技创新推动经济发展", "source": "科技日报", "time": "2026-04-25"},
                    {"title": "全球气候峰会达成新协议", "source": "环球时报", "time": "2026-04-24"},
                    {"title": "新能源汽车销量创新高", "source": "汽车周刊", "time": "2026-04-23"}
                ],
                "tech": [
                    {"title": "AI助手成为日常生活标配", "source": "人工智能杂志", "time": "2026-04-25"},
                    {"title": "量子计算机取得突破性进展", "source": "科学前沿", "time": "2026-04-24"},
                    {"title": "5G网络覆盖全国所有城市", "source": "通信世界", "time": "2026-04-23"}
                ],
                "sports": [
                    {"title": "世界杯预选赛中国队获胜", "source": "体育周报", "time": "2026-04-25"},
                    {"title": "NBA季后赛进入白热化阶段", "source": "篮球天地", "time": "2026-04-24"}
                ]
            }

            articles = news_data.get(category, news_data["general"])[:count]
            return json.dumps({
                "category": category,
                "articles": articles
            }, ensure_ascii=False, indent=2)

        self.tools["execute_python"] = Tool(
            name="execute_python",
            description="Execute Python code and return the result. Use this for calculations, data processing, or any task requiring code execution.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute"
                    }
                },
                "required": ["code"]
            },
            handler=execute_python
        )

        self.tools["get_current_time"] = Tool(
            name="get_current_time",
            description="Get the current date and time.",
            parameters={
                "type": "object",
                "properties": {}
            },
            handler=get_current_time
        )

        self.tools["calculate"] = Tool(
            name="calculate",
            description="Calculate a mathematical expression. Supports +, -, *, /, and parentheses.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to calculate"
                    }
                },
                "required": ["expression"]
            },
            handler=calculate
        )

        self.tools["get_weather"] = Tool(
            name="get_weather",
            description="Get current weather information for a location.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city or location name to get weather for"
                    }
                },
                "required": ["location"]
            },
            handler=get_weather
        )

        self.tools["get_coordinates"] = Tool(
            name="get_coordinates",
            description="Get latitude and longitude coordinates for an address or place name.",
            parameters={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "The address or place name to get coordinates for"
                    }
                },
                "required": ["address"]
            },
            handler=get_coordinates
        )

        self.tools["search_places"] = Tool(
            name="search_places",
            description="Search for places by keyword or category.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search keyword or category"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
            handler=search_places
        )

        self.tools["translate_text"] = Tool(
            name="translate_text",
            description="Translate text to another language.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to translate"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "Target language code (e.g., 'en', 'zh', 'ja', 'fr', 'es')",
                        "default": "en"
                    }
                },
                "required": ["text"]
            },
            handler=translate_text
        )

        self.tools["get_news"] = Tool(
            name="get_news",
            description="Get latest news articles by category.",
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "News category (e.g., 'general', 'tech', 'sports')",
                        "default": "general"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of articles to return (default: 3)",
                        "default": 3
                    }
                },
                "required": []
            },
            handler=get_news
        )

    def _build_messages(self, user_text: str) -> List[Dict[str, Any]]:
        """Build message list for API call."""
        msgs = [{"role": "system", "content": self.system_prompt}]
        for msg in self.messages:
            msgs.append(msg.to_dict())
        msgs.append({"role": "user", "content": user_text})
        return msgs

    def _get_tools_for_api(self) -> Optional[List[Dict[str, Any]]]:
        """Get tools in API-compatible format."""
        if not self.enable_tools or not self.tools:
            return None
        return [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        } for tool in self.tools.values()]

    async def _execute_tool(self, tool_call: Dict[str, Any], approval_id: Optional[str] = None) -> str:
        """Execute a tool call and return the result."""
        function_name = tool_call.get("function", {}).get("name")
        arguments = tool_call.get("function", {}).get("arguments", "{}")

        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            return "Error: Invalid arguments"

        if function_name not in self.tools:
            return f"Error: Unknown tool '{function_name}'"

        tool = self.tools[function_name]
        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**args)
            else:
                result = tool.handler(**args)
            return str(result)
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"

    async def chat_stream(
        self,
        user_text: str,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream SSE-formatted chat response with optional reasoning and tool support."""
        rid = f"resp_{uuid.uuid4().hex[:8]}"
        mid = f"msg_{uuid.uuid4().hex[:8]}"
        now = int(time.time())
        text = ""
        reasoning = ""

        api_msgs = self._build_messages(user_text)

        # Send initial events
        yield sse(0, "response", "created", {"id": rid, "created_at": now, "session_id": session_id})
        yield sse(1, "response", "in_progress", {"id": rid})
        yield sse(2, "message", "in_progress", {"id": mid, "role": "assistant"})

        n = 3

        # Initialize tool_results at the beginning of chat_stream
        tool_results = []
        tool_calls_list = []

        try:
            # Prepare API call arguments
            call_args = {
                "model": config.MODEL_NAME,
                "messages": api_msgs,
                "stream": True,
            }

            # Add reasoning if enabled (DeepSeek specific)
            if self.enable_reasoning:
                call_args["extra_body"] = {
                    "thinking": {"type": "enabled"},
                    "reasoning_effort": "high",
                }

            # Add tools if enabled
            tools = self._get_tools_for_api()
            if tools:
                call_args["tools"] = tools
                call_args["tool_choice"] = "auto"

            stream = await self.client.chat.completions.create(**call_args)

            # Track tool calls
            tool_calls_buffer: Dict[int, Dict[str, Any]] = {}
            in_reasoning = False

            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                # Handle reasoning content (DeepSeek R1)
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    if not in_reasoning:
                        in_reasoning = True
                        yield sse(n, "content", "in_progress", {
                            "type": "reasoning",
                            "delta": True,
                            "msg_id": mid,
                            "text": ""
                        })
                        n += 1
                    reasoning += delta.reasoning_content
                    yield sse(n, "content", "in_progress", {
                        "type": "reasoning",
                        "delta": True,
                        "msg_id": mid,
                        "text": delta.reasoning_content
                    })
                    n += 1

                # Handle tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        index = tc.index
                        if index not in tool_calls_buffer:
                            tool_calls_buffer[index] = {
                                "id": tc.id or "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            }
                        if tc.function:
                            if tc.function.name:
                                tool_calls_buffer[index]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                tool_calls_buffer[index]["function"]["arguments"] += tc.function.arguments

                # Handle regular content
                if delta.content:
                    text += delta.content
                    yield sse(n, "content", "in_progress", {
                        "type": "text",
                        "delta": True,
                        "msg_id": mid,
                        "text": delta.content
                    })
                    n += 1

            # Execute tools if any were called
            if tool_calls_buffer:
                tool_calls_list = [tool_calls_buffer[i] for i in sorted(tool_calls_buffer.keys())]

                # 首先，将AI的回复（包含tool_calls）添加到消息历史
                # 这是必需的，因为 tool 角色消息必须响应一个包含 tool_calls 的 assistant 消息
                assistant_msg_with_tools = {
                    "role": "assistant",
                    "content": text if text else None,
                    "tool_calls": [
                        {
                            "id": tc.get("id", ""),
                            "type": "function",
                            "function": {
                                "name": tc.get("function", {}).get("name", ""),
                                "arguments": tc.get("function", {}).get("arguments", "{}")
                            }
                        } for tc in tool_calls_list
                    ]
                }
                api_msgs.append(assistant_msg_with_tools)

                # Notify about tool calls
                yield sse(n, "content", "in_progress", {
                    "type": "tool_calls",
                    "tool_calls": tool_calls_list
                })
                n += 1

                # Execute tools and collect results
                tool_results = []
                for tc in tool_calls_list:
                    func_name = tc.get("function", {}).get("name", "")
                    func_args = tc.get("function", {}).get("arguments", "{}")

                    # Check if this tool requires approval
                    requires_approval = func_name in self.tools_require_approval

                    if requires_approval:
                        # Create approval request
                        approval_id = create_approval_request(func_name, json.loads(func_args) if isinstance(func_args, str) else func_args)

                        # Send approval request event (包含完整的工具调用信息)
                        yield sse(n, "content", "in_progress", {
                            "type": "approval_request",
                            "approval_id": approval_id,
                            "tool_call": tc  # 发送完整的工具调用信息
                        })
                        n += 1

                        # Wait for user approval
                        is_approved = await wait_for_approval(approval_id, timeout=300.0)

                        # Send approval result事件（包含工具信息，前端用它来显示工具卡片）
                        yield sse(n, "content", "in_progress", {
                            "type": "approval_result",
                            "approval_id": approval_id,
                            "approved": is_approved,
                            "tool_call": tc if is_approved else None  # 只有批准时才发送工具信息
                        })
                        n += 1

                        if not is_approved:
                            # User rejected or timed out
                            result = f"Tool execution rejected by user"
                            tool_results.append({
                                "tool_call_id": tc.get("id", ""),
                                "role": "tool",
                                "name": func_name,
                                "content": result
                            })
                            yield sse(n, "content", "in_progress", {
                                "type": "tool_result",
                                "tool_name": func_name,
                                "result": result
                            })
                            n += 1
                            continue

                    # Execute the tool (只有在批准后或不需要审批的工具)
                    result = await self._execute_tool(tc)
                    tool_results.append({
                        "tool_call_id": tc.get("id", ""),
                        "role": "tool",
                        "name": func_name,
                        "content": result
                    })

                    yield sse(n, "content", "in_progress", {
                        "type": "tool_result",
                        "tool_name": func_name,
                        "result": result
                    })
                    n += 1

                # Continue conversation with tool results
                for tr in tool_results:
                    api_msgs.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_call_id"],
                        "content": tr["content"]
                    })

                # Get final response after tool execution
                logger.info(f"Second API call messages: {json.dumps(api_msgs, ensure_ascii=False, indent=2)}")
                final_call_args = {
                    "model": config.MODEL_NAME,
                    "messages": api_msgs,
                    "stream": True,
                }

                if self.enable_reasoning:
                    final_call_args["extra_body"] = {
                        "thinking": {"type": "enabled"},
                        "reasoning_effort": "high",
                    }

                final_stream = await self.client.chat.completions.create(**final_call_args)

                async for chunk in final_stream:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta
                    if delta.content:
                        text += delta.content
                        yield sse(n, "content", "in_progress", {
                            "type": "text",
                            "delta": True,
                            "msg_id": mid,
                            "text": delta.content
                        })
                        n += 1

        except Exception as e:
            yield sse(n, "error", "error", {"error": str(e)})
            return

        # Send completion events
        yield sse(n, "content", "completed", {"type": "text", "text": text})

        content_list = [{"type": "text", "text": text}]
        if reasoning:
            content_list.insert(0, {"type": "reasoning", "text": reasoning})

        yield sse(n + 1, "message", "completed", {
            "id": mid,
            "role": "assistant",
            "content": content_list
        })
        yield sse(n + 2, "response", "completed", {
            "id": rid,
            "created_at": now,
            "completed_at": int(time.time()),
            "output": [{"role": "assistant", "content": content_list}]
        })

        # Update conversation history
        self.messages.append(ChatMessage("user", user_text))

        # Save assistant message with tool_calls and all tool results
        if tool_calls_buffer:
            tool_calls_for_history = [
                {
                    "id": tc.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": tc.get("function", {}).get("arguments", "{}")
                    }
                } for tc in tool_calls_list
            ]
            self.messages.append(ChatMessage(
                "assistant",
                text if text else "",
                reasoning if self.enable_reasoning else None,
                tool_calls=tool_calls_for_history
            ))
            # Save each tool result for multi-turn persistence
            for tr in tool_results:
                self.messages.append(ChatMessage(
                    role="tool",
                    content=tr["content"],
                    tool_call_id=tr["tool_call_id"]
                ))
        else:
            self.messages.append(ChatMessage("assistant", text, reasoning if self.enable_reasoning else None))

    def clear(self):
        """Clear conversation history."""
        self.messages = []

    def set_system_prompt(self, prompt: str):
        """Update the system prompt."""
        self.system_prompt = prompt


def sse(seq: int, obj: str, status: str, data: dict) -> str:
    """Format SSE event."""
    return f"data: {json.dumps({'sequence_number': seq, 'object': obj, 'status': status, **data}, ensure_ascii=False)}\n\n"


# Session management
_agents: Dict[str, SimpleChatAgent] = {}


def get_agent(session_id: Optional[str] = None, enable_reasoning: bool = False, enable_tools: bool = False, tools_require_approval: List[str] = None) -> SimpleChatAgent:
    """Get or create an agent for the session."""
    sid = session_id or "default"
    if sid not in _agents:
        _agents[sid] = SimpleChatAgent(
            enable_reasoning=enable_reasoning,
            enable_tools=enable_tools,
            tools_require_approval=tools_require_approval
        )
    return _agents[sid]


def clear_session(session_id: Optional[str] = None):
    """Clear session memory."""
    sid = session_id or "default"
    if sid in _agents:
        _agents[sid].clear()


def get_session_ids() -> List[str]:
    """Get all active session IDs."""
    return list(_agents.keys())
