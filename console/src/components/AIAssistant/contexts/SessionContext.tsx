import React, { createContext, useContext, useState, useCallback } from 'react';
import { v2SessionApi } from '../sessionApi';

export interface ExtendedChatSession {
  id: string;
  name: string;
  messages?: any[];
  createdAt?: string;
  pinned?: boolean;
  generating?: boolean;
  [key: string]: any;
}

export interface ApprovalRequest {
  approvalId: string;
  toolName: string;
  toolArgs?: string;
}

interface SessionsState {
  sessions: ExtendedChatSession[];
  currentSessionId: string | undefined;
  setCurrentSessionId: (id: string | undefined) => void;
  setSessions: (sessions: ExtendedChatSession[]) => void;
  pendingApproval: ApprovalRequest | null;
  setPendingApproval: (approval: ApprovalRequest | null) => void;
}

interface SessionsActions {
  createSession: (data?: { name?: string }) => Promise<string>;
}

const SessionsStateContext = createContext<SessionsState | null>(null);
const SessionsActionsContext = createContext<SessionsActions | null>(null);

export function V2SessionProvider({ children }: { children: React.ReactNode }) {
  const [sessions, setSessions] = useState<ExtendedChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(undefined);
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);

  const createSession = useCallback(async (data?: { name?: string }) => {
    const session = await v2SessionApi.createSession(data);
    setSessions((prev) => [session, ...prev]);
    setCurrentSessionId(session.id);
    return session.id;
  }, []);

  return (
    <SessionsStateContext.Provider
      value={{ sessions, currentSessionId, setCurrentSessionId, setSessions, pendingApproval, setPendingApproval }}
    >
      <SessionsActionsContext.Provider value={{ createSession }}>
        {children}
      </SessionsActionsContext.Provider>
    </SessionsStateContext.Provider>
  );
}

export function useSessionsState(): SessionsState {
  const ctx = useContext(SessionsStateContext);
  if (!ctx) throw new Error('useSessionsState must be used within V2SessionProvider');
  return ctx;
}

export function useSessions(): SessionsActions {
  const ctx = useContext(SessionsActionsContext);
  if (!ctx) throw new Error('useSessions must be used within V2SessionProvider');
  return ctx;
}
