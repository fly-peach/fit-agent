import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Drawer } from "antd";
import { IconButton } from "@agentscope-ai/design";
import { SparkOperateRightLine } from "@agentscope-ai/icons";
import {
  useChatAnywhereSessionsState,
  useChatAnywhereSessions,
  type IAgentScopeRuntimeWebUISession,
} from "@agentscope-ai/chat";
import sessionApi from "../../sessionApi";
import ChatSessionItem from "../ChatSessionItem";
import styles from "./index.module.less";

interface ExtendedChatSession extends IAgentScopeRuntimeWebUISession {
  createdAt?: string | null;
  pinned?: boolean;
  generating?: boolean;
}

interface ChatSessionDrawerProps {
  open: boolean;
  onClose: () => void;
}

const formatCreatedAt = (raw: string | null | undefined): string => {
  if (!raw) return "";
  const date = new Date(raw);
  if (isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate(),
  )} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(
    date.getSeconds(),
  )}`;
};

const ChatSessionDrawer: React.FC<ChatSessionDrawerProps> = (props) => {
  const { sessions, currentSessionId, setCurrentSessionId, setSessions } =
    useChatAnywhereSessionsState();

  const { createSession } = useChatAnywhereSessions();

  const handleCreateSession = useCallback(async () => {
    await createSession();
    props.onClose();
  }, [createSession, props.onClose]);

  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const sortedSessions = useMemo(() => {
    return [...sessions].sort((a, b) => {
      const extA = a as ExtendedChatSession;
      const extB = b as ExtendedChatSession;

      if (extA.pinned && !extB.pinned) return -1;
      if (!extA.pinned && extB.pinned) return 1;

      const aTime = extA.createdAt;
      const bTime = extB.createdAt;
      if (!aTime && !bTime) return 0;
      if (!aTime) return 1;
      if (!bTime) return -1;
      return new Date(bTime).getTime() - new Date(aTime).getTime();
    });
  }, [sessions]);

  const refreshSessions = useCallback(async () => {
    const list = await sessionApi.getSessionList();
    setSessions(list);
  }, [setSessions]);

  useEffect(() => {
    if (!props.open) return;

    let isCancelled = false;

    const fetchSessions = async () => {
      try {
        const list = await sessionApi.getSessionList();
        if (!isCancelled) {
          setSessions(list);
        }
      } catch (error) {
        console.error("Failed to refresh session list:", error);
      }
    };

    void fetchSessions();

    return () => {
      isCancelled = true;
    };
  }, [props.open, setSessions]);

  const handleSessionClick = useCallback(
    (sessionId: string) => {
      setCurrentSessionId(sessionId);
    },
    [setCurrentSessionId],
  );

  const handleDelete = useCallback(
    async (sessionId: string) => {
      await sessionApi.removeSession({ id: sessionId });

      if (currentSessionId === sessionId) {
        const list = await sessionApi.getSessionList();
        setCurrentSessionId(list[0]?.id);
      }

      await refreshSessions();
    },
    [currentSessionId, setCurrentSessionId, refreshSessions],
  );

  const handleEditStart = useCallback(
    (sessionId: string, currentName: string) => {
      setEditingSessionId(sessionId);
      setEditValue(currentName);
    },
    [],
  );

  const handleEditChange = useCallback((value: string) => {
    setEditValue(value);
  }, []);

  const handleEditSubmit = useCallback(async () => {
    if (!editingSessionId) return;

    const newName = editValue.trim();
    if (newName) {
      await sessionApi.updateSession({ id: editingSessionId, name: newName });
    }

    setEditingSessionId(null);
    setEditValue("");
    await refreshSessions();
  }, [editingSessionId, editValue, refreshSessions]);

  const handleEditCancel = useCallback(() => {
    setEditingSessionId(null);
    setEditValue("");
  }, []);

  const handlePinToggle = useCallback(
    async (sessionId: string) => {
      const session = sessions.find((s) => s.id === sessionId) as
        | ExtendedChatSession
        | undefined;

      if (session) {
        try {
          const newPinnedState = !session.pinned;
          await sessionApi.updateSession({
            id: sessionId,
            pinned: newPinnedState,
          } as any);
          await refreshSessions();
        } catch (error) {
          console.error("Failed to toggle pin status:", error);
        }
      }
    },
    [sessions, refreshSessions],
  );

  return (
    <Drawer
      open={props.open}
      onClose={props.onClose}
      placement="right"
      width={360}
      closable={false}
      title={null}
      styles={{
        header: { display: "none" },
        body: {
          padding: 0,
          display: "flex",
          flexDirection: "column",
          height: "100%",
          overflow: "hidden",
        },
        mask: { background: "transparent" },
      }}
      className={styles.drawer}
    >
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerTitle}>All Chats</span>
        </div>
        <div className={styles.headerRight}>
          <IconButton
            bordered={false}
            icon={<SparkOperateRightLine />}
            onClick={props.onClose}
          />
        </div>
      </div>

      <div className={styles.createSection}>
        <div className={styles.createButton} onClick={handleCreateSession}>
          New Chat
        </div>
      </div>

      <div className={styles.listWrapper}>
        <div className={styles.topGradient} />
        <div className={styles.list}>
          {sortedSessions.map((session) => {
            const ext = session as ExtendedChatSession;
            return (
              <ChatSessionItem
                key={session.id}
                name={session.name || "New Chat"}
                time={formatCreatedAt(ext.createdAt ?? null)}
                pinned={ext.pinned}
                active={session.id === currentSessionId}
                editing={editingSessionId === session.id}
                editValue={
                  editingSessionId === session.id ? editValue : undefined
                }
                onClick={() => handleSessionClick(session.id!)}
                onEdit={() =>
                  handleEditStart(session.id!, session.name || "New Chat")
                }
                onDelete={() => handleDelete(session.id!)}
                onPin={() => handlePinToggle(session.id!)}
                onEditChange={handleEditChange}
                onEditSubmit={handleEditSubmit}
                onEditCancel={handleEditCancel}
              />
            );
          })}
        </div>
        <div className={styles.bottomGradient} />
      </div>
    </Drawer>
  );
};

export default ChatSessionDrawer;
