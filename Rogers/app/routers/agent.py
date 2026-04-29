import os

from agentscope.pipeline import stream_printing_messages
from src.agents.agent import rogers_agent
from agentscope_runtime.engine.app import AgentApp
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest






# 创建 AgentApp
agent_app = AgentApp(
    app_name="MyAssistant",
    app_description="A helpful assistant agent",
)

@agent_app.query(framework="agentscope")
async def query_func(
    self,
    msgs,
    request: AgentRequest | None = None,
    **kwargs,
):
    """处理用户查询。"""
    assert request is not None, "request is required"
    session_id = request.session_id
    user_id = request.user_id

    agent = rogers_agent
    agent.set_console_output_enabled(False)

    await agent_app.state.session.load_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent,
    )

    async for msg, last, *_ in stream_printing_messages(
        agents=[agent],
        coroutine_task=agent(msgs),
    ):
        yield msg, last

    await agent_app.state.session.save_session_state(
        session_id=session_id,
        user_id=user_id,
        agent=agent,
    )


