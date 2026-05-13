import {
  IAgentScopeRuntimeWebUISession,
  IAgentScopeRuntimeWebUISessionAPI,
} from '@agentscope-ai/chat';

/**
 * 从 source 字符串提取子 Agent 名称，如 "[SubAgent] DietAnalyst" → "DietAnalyst"
 */
const extractSubAgentName = (source: string): string | null => {
  const match = source.match(/^\[SubAgent\]\s+(.+)$/);
  return match?.[1] || null;
};

/**
 * 将 output 数组中 SubAgent 消息的 type 从 "message" 改为 "plugin_call"，
 * 构造与 responseParser 一致的格式。
 * 用于回溯旧会话中保存到 localStorage 的数据。
 */
const convertSubAgentOutput = (output: Record<string, any>[]) => {
  for (const msg of output) {
    const src = msg.metadata?.source;
    if (msg.type === 'message' && typeof src === 'string' && src.startsWith('[SubAgent]')) {
      const agentName = extractSubAgentName(src) || '分析';
      let combinedText = '';
      for (const c of msg.content || []) {
        if (c.type === 'text' && c.text) combinedText += c.text;
      }
      msg.type = 'plugin_call';
      msg.content = [
        { type: 'data', data: { name: 'sub_agent_analysis', agentName } },
        { type: 'data', data: { output: combinedText } },
      ];
    }
  }
};

/**
 * 遍历会话消息的 cards，查找 AgentScopeRuntimeResponseCard.data.output
 * 并进行 SubAgent 转换。
 */
const convertSessionMessages = (messages: any[]) => {
  for (const msg of messages) {
    for (const card of msg.cards || []) {
      if (card.code === 'AgentScopeRuntimeResponseCard' && Array.isArray(card.data?.output)) {
        convertSubAgentOutput(card.data.output);
      }
    }
  }
};

class SessionApi implements IAgentScopeRuntimeWebUISessionAPI {
  private lsKey: string;
  private sessionList: IAgentScopeRuntimeWebUISession[];

  constructor() {
    this.lsKey = 'agent-scope-runtime-webui-sessions';
    this.sessionList = [];
  }

  async getSessionList() {
    const raw = localStorage.getItem(this.lsKey);
    this.sessionList = JSON.parse(raw || '[]');
    // 回溯转换旧会话中的 SubAgent 消息
    for (const session of this.sessionList) {
      if (session.messages?.length) {
        convertSessionMessages(session.messages);
      }
    }
    return [...this.sessionList];
  }

  async getSession(sessionId: string) {
    const session = this.sessionList.find((s) => s.id === sessionId);
    if (session?.messages?.length) {
      convertSessionMessages(session.messages);
    }
    return session as IAgentScopeRuntimeWebUISession;
  }

  async updateSession(session: Partial<IAgentScopeRuntimeWebUISession>) {
    const index = this.sessionList.findIndex((item) => item.id === session.id);
    if (index > -1) {
      this.sessionList[index] = {
        ...this.sessionList[index],
        ...session,
      };
      localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    }

    return [...this.sessionList];
  }

  async createSession(session: Partial<IAgentScopeRuntimeWebUISession>) {
    session.id = Date.now().toString();
    this.sessionList.unshift(session as IAgentScopeRuntimeWebUISession);
    localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    return [...this.sessionList];
  }

  async removeSession(session: Partial<IAgentScopeRuntimeWebUISession>) {
    this.sessionList = this.sessionList.filter(
      (item) => item.id !== session.id,
    );
    localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    return [...this.sessionList];
  }
}

export default new SessionApi();
