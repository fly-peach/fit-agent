import { ChatMessage } from '../types';

const LS_KEY = 'agent-scope-runtime-webui-sessions';

class V2SessionApi {
  private lsKey: string = LS_KEY;
  private sessionList: any[] = [];

  reset() {
    this.sessionList = [];
  }

  async getSessionList(): Promise<any[]> {
    const raw = localStorage.getItem(this.lsKey);
    this.sessionList = JSON.parse(raw || '[]');

    for (const session of this.sessionList) {
      if (session.messages?.length) {
        for (const msg of session.messages) {
          for (const card of msg.cards || []) {
            if (card.code === 'AgentScopeRuntimeResponseCard' && Array.isArray(card.data?.output)) {
              for (const outMsg of card.data.output) {
                if (
                  outMsg.type === 'message' &&
                  outMsg.metadata?.source?.startsWith('[SubAgent]')
                ) {
                  const match = outMsg.metadata.source.match(/^\[SubAgent\]\s+(.+)$/);
                  const agentName = match?.[1] || '分析';
                  let combinedText = '';
                  for (const c of outMsg.content || []) {
                    if (c.type === 'text' && c.text) combinedText += c.text;
                  }
                  outMsg.type = 'plugin_call';
                  outMsg.content = [
                    { type: 'data', data: { name: 'sub_agent_analysis', agentName } },
                    { type: 'data', data: { output: combinedText } },
                  ];
                }
              }
            }
          }
        }
      }
    }

    return [...this.sessionList];
  }

  async getSession(sessionId: string): Promise<any> {
    const session = this.sessionList.find((s) => s.id === sessionId);
    return session || null;
  }

  async createSession(sessionData?: { name?: string }): Promise<any> {
    const session: any = {
      id: Date.now().toString(),
      name: sessionData?.name || 'New Chat',
      messages: [],
      createdAt: new Date().toISOString(),
      pinned: false,
      generating: false,
    };
    this.sessionList.unshift(session);
    localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    return session;
  }

  async updateSession(session: Partial<any>): Promise<any> {
    this.sessionList = JSON.parse(localStorage.getItem(this.lsKey) || '[]');
    const index = this.sessionList.findIndex((s) => s.id === session.id);
    if (index > -1) {
      this.sessionList[index] = { ...this.sessionList[index], ...session };
      localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    }
    return [...this.sessionList];
  }

  async removeSession(session: Partial<any>): Promise<any> {
    this.sessionList = JSON.parse(localStorage.getItem(this.lsKey) || '[]');
    this.sessionList = this.sessionList.filter((s) => s.id !== session.id);
    localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    return [...this.sessionList];
  }

  async saveSessionMessages(sessionId: string, messages: ChatMessage[]): Promise<void> {
    const raw = localStorage.getItem(this.lsKey);
    this.sessionList = JSON.parse(raw || '[]');
    const index = this.sessionList.findIndex((s) => s.id === sessionId);
    if (index > -1) {
      const storedMessages = messages.map(convertV2MessageToStored);
      this.sessionList[index].messages = storedMessages;
      this.sessionList[index]._messages = messages.map(m => ({
        id: m.id,
        role: m.role,
        content: m.content,
        ...(m.response ? { response: m.response } : {}),
        createdAt: m.createdAt,
      }));
      localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    }
  }
}

function convertV2MessageToStored(msg: ChatMessage): any {
  if (msg.role === 'user') {
    return {
      id: msg.id,
      role: 'user',
      cards: [
        {
          code: 'AgentScopeRuntimeRequestCard',
          data: {
            input: [{
              role: 'user',
              type: 'message',
              content: msg.content,
            }],
          },
        },
      ],
      msgStatus: msg.status,
    };
  }

  return {
    id: msg.id,
    role: 'assistant',
    cards: msg.response ? [
      {
        code: 'AgentScopeRuntimeResponseCard',
        data: msg.response,
      },
    ] : [],
    msgStatus: msg.status,
  };
}

export const v2SessionApi = new V2SessionApi();
