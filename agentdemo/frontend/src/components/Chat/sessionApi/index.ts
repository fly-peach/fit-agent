import {
  IAgentScopeRuntimeWebUISession,
  IAgentScopeRuntimeWebUISessionAPI,
} from '@agentscope-ai/chat';

interface ExtendedSession extends IAgentScopeRuntimeWebUISession {
  createdAt?: string | null;
  pinned?: boolean;
  _messages?: any[];
}

class SessionApi implements IAgentScopeRuntimeWebUISessionAPI {
  private lsKey: string;
  private sessionList: ExtendedSession[];

  constructor() {
    this.lsKey = 'agent-scope-runtime-webui-sessions';
    this.sessionList = [];
  }

  async getSessionList() {
    this.sessionList = JSON.parse(localStorage.getItem(this.lsKey) || '[]');
    return [...this.sessionList] as IAgentScopeRuntimeWebUISession[];
  }

  async getSession(sessionId: string) {
    return this.sessionList.find((session) => session.id === sessionId) as IAgentScopeRuntimeWebUISession;
  }

  async updateSession(session: Partial<IAgentScopeRuntimeWebUISession>) {
    const index = this.sessionList.findIndex((item) => item.id === session.id);
    if (index > -1) {
      this.sessionList[index] = {
        ...this.sessionList[index],
        ...session,
      } as ExtendedSession;
      localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    }

    return [...this.sessionList] as IAgentScopeRuntimeWebUISession[];
  }

  async createSession(session: Partial<IAgentScopeRuntimeWebUISession>) {
    session.id = Date.now().toString();
    const extended: ExtendedSession = {
      ...session,
      createdAt: new Date().toISOString(),
      pinned: false,
      _messages: [],
    } as ExtendedSession;
    this.sessionList.unshift(extended);
    localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    return [...this.sessionList] as IAgentScopeRuntimeWebUISession[];
  }

  async removeSession(session: Partial<IAgentScopeRuntimeWebUISession>) {
    this.sessionList = this.sessionList.filter(
      (item) => item.id !== session.id,
    );
    localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    return [...this.sessionList] as IAgentScopeRuntimeWebUISession[];
  }

  /** Store messages for a session (used by search) */
  async storeMessages(sessionId: string, messages: any[]) {
    const index = this.sessionList.findIndex((item) => item.id === sessionId);
    if (index > -1) {
      this.sessionList[index]._messages = messages;
      localStorage.setItem(this.lsKey, JSON.stringify(this.sessionList));
    }
  }
}

export default new SessionApi();
