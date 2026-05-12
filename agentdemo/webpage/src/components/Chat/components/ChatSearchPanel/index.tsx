import React, { useState, useCallback, useRef, useEffect } from "react";
import { Drawer, Input, List, Typography, Empty, Spin } from "antd";
import type { InputRef } from "antd";
import { IconButton } from "@agentscope-ai/design";
import { SparkOperateRightLine, SparkSearchLine } from "@agentscope-ai/icons";
import { useChatAnywhereSessionsState } from "@agentscope-ai/chat";
import sessionApi from "../../sessionApi";
import styles from "./index.module.less";

interface ChatSearchPanelProps {
  open: boolean;
  onClose: () => void;
}

const extractTextFromContent = (content: unknown): string => {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return (content as Array<{ type: string; text?: string }>)
    .filter((c) => c.type === "text" && c.text)
    .map((c) => c.text || "")
    .join("\n");
};

interface SearchResult {
  sessionId: string;
  sessionName: string;
  role: string;
  roleLabel: string;
  text: string;
  matchedText: string;
  timestamp?: string | null;
}

const formatTimestamp = (raw: string | null | undefined): string => {
  if (!raw) return "";
  const date = new Date(raw);
  if (isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate(),
  )} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
};

const ChatSearchPanel: React.FC<ChatSearchPanelProps> = ({ open, onClose }) => {
  const { setCurrentSessionId } = useChatAnywhereSessionsState();
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const inputRef = useRef<InputRef>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const searchSeqRef = useRef(0);

  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (open) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    } else {
      setSearchQuery("");
      setSearchResults([]);
    }
  }, [open]);

  useEffect(() => {
    const seq = ++searchSeqRef.current;

    if (!searchQuery.trim()) {
      setSearchResults([]);
      setLoading(false);
      return;
    }

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const query = searchQuery.toLowerCase();
        const results: SearchResult[] = [];

        const allSessions = await sessionApi.getSessionList();
        if (seq !== searchSeqRef.current) return;

        for (const session of allSessions) {
          const sessionId = session.id || "";
          const sessionName = session.name || "New Chat";
          const messages = (session as any)._messages || [];

          if (sessionName.toLowerCase().includes(query)) {
            results.push({
              sessionId,
              sessionName,
              role: "title",
              roleLabel: "Title",
              text: sessionName,
              matchedText: sessionName,
              timestamp: (session as any).createdAt,
            });
          }

          for (const msg of messages) {
            const text = extractTextFromContent(msg.content);
            const lowerText = text.toLowerCase();
            if (lowerText.includes(query)) {
              const matchIndex = lowerText.indexOf(query);
              const contextLength = 80;
              const start = Math.max(0, matchIndex - contextLength);
              const end = Math.min(
                text.length,
                matchIndex + searchQuery.length + contextLength,
              );
              const matchedText = text.slice(start, end);

              results.push({
                sessionId,
                sessionName,
                role: msg.role || "",
                roleLabel: msg.role === "user" ? "User" : "Assistant",
                text,
                matchedText: start > 0 ? `...${matchedText}` : matchedText,
                timestamp: (session as any).createdAt,
              });
            }
          }
        }

        if (seq !== searchSeqRef.current) return;
        setSearchResults(results);
      } catch (err) {
        if (seq !== searchSeqRef.current) return;
        console.error("Search failed:", err);
        setSearchResults([]);
      } finally {
        if (seq === searchSeqRef.current) {
          setLoading(false);
        }
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  const handleResultClick = useCallback(
    (result: SearchResult) => {
      setCurrentSessionId(result.sessionId);
      onClose();
    },
    [setCurrentSessionId, onClose],
  );

  return (
    <Drawer
      open={open}
      onClose={onClose}
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
          <span className={styles.headerTitle}>Search Chats</span>
        </div>
        <div className={styles.headerRight}>
          <IconButton
            bordered={false}
            icon={<SparkOperateRightLine />}
            onClick={onClose}
          />
        </div>
      </div>

      <div className={styles.searchSection}>
        <Input
          ref={inputRef}
          placeholder="Search in chats..."
          prefix={<SparkSearchLine style={{ color: "rgba(0,0,0,0.25)" }} />}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          allowClear
          className={styles.searchInput}
        />
      </div>

      {searchQuery.trim() && !loading && (
        <div className={styles.resultsCount}>
          <Typography.Text type="secondary">
            {searchResults.length} result{searchResults.length !== 1 ? "s" : ""}
          </Typography.Text>
        </div>
      )}

      <div className={styles.listWrapper}>
        <div className={styles.topGradient} />
        <div className={styles.list}>
          {loading ? (
            <div
              style={{ display: "flex", justifyContent: "center", padding: 40 }}
            >
              <Spin />
            </div>
          ) : searchQuery.trim() && searchResults.length === 0 ? (
            <Empty description="No results found" style={{ marginTop: 40 }} />
          ) : (
            <List
              dataSource={searchResults}
              renderItem={(item) => (
                <div
                  className={styles.searchResultItem}
                  onClick={() => handleResultClick(item)}
                >
                  <div className={styles.resultHeader}>
                    <span className={styles.resultChatName}>
                      {item.sessionName}
                    </span>
                    <span className={styles.resultRole}>{item.roleLabel}</span>
                  </div>
                  <div className={styles.resultContent}>
                    <Typography.Text ellipsis style={{ fontSize: 13 }}>
                      {item.matchedText}
                    </Typography.Text>
                  </div>
                  {item.timestamp && (
                    <div className={styles.resultTime}>
                      {formatTimestamp(item.timestamp)}
                    </div>
                  )}
                </div>
              )}
            />
          )}
        </div>
        <div className={styles.bottomGradient} />
      </div>
    </Drawer>
  );
};

export default ChatSearchPanel;
