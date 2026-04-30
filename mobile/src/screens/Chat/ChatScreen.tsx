import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { GiftedChat, IMessage, Send, Bubble, InputToolbar } from 'react-native-gifted-chat';
import { chatService } from '../../services/chat';
import { COLORS } from '../../constants';
import type { ChatSession } from '../../types';

const BOT_USER = { _id: 2, name: 'Rogers', avatar: '🤖' };
const QUICK_PROMPTS = [
  '帮我制定一个减脂训练计划',
  '今天应该吃多少蛋白质？',
  '如何提高跑步耐力？',
];

export default function ChatScreen() {
  const [messages, setMessages] = useState<IMessage[]>([]);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(false);
  const isStreaming = useRef(false);

  useEffect(() => {
    initSession();
  }, []);

  const initSession = async () => {
    try {
      let sessions = await chatService.getSessions();
      let current: ChatSession;
      if (sessions.length > 0) {
        current = sessions[0];
      } else {
        current = await chatService.createSession();
      }
      setSession(current);

      // Convert stored messages to GiftedChat format
      const gifted = current.messages.map((m, i) => ({
        _id: `${current.id}-${i}`,
        text: m.content,
        createdAt: new Date(current.createdAt),
        user: m.role === 'user' ? { _id: 1 } : BOT_USER,
      })).reverse();
      setMessages(gifted);
    } catch {
      const s = await chatService.createSession();
      setSession(s);
    }
  };

  const handleNewChat = async () => {
    const s = await chatService.createSession();
    setSession(s);
    setMessages([]);
  };

  const onSend = useCallback(async (newMessages: IMessage[]) => {
    const userMsg = newMessages[0];
    setMessages((prev) => GiftedChat.append(prev, newMessages));

    if (!session) return;

    // Save user message
    await chatService.addMessage(session.id, {
      role: 'user',
      content: userMsg.text,
    });

    setLoading(true);

    // Add placeholder assistant message
    const botMsgId = `${Date.now()}-bot`;
    const botMsg: IMessage = {
      _id: botMsgId,
      text: '',
      createdAt: new Date(),
      user: BOT_USER,
    };
    setMessages((prev) => GiftedChat.append(prev, [botMsg]));

    let fullText = '';

    try {
      // Try streaming first
      await chatService.sendMessageStream(
        userMsg.text,
        session.id,
        (chunk) => {
          fullText += chunk;
          isStreaming.current = true;
          setMessages((prev) =>
            prev.map((m) => (m._id === botMsgId ? { ...m, text: fullText } : m))
          );
        },
        async () => {
          isStreaming.current = false;
          // Save assistant message
          await chatService.addMessage(session.id, {
            role: 'assistant',
            content: fullText,
          });
          setLoading(false);
        },
        async () => {
          isStreaming.current = false;
          // Fallback to non-streaming if stream fails
          try {
            const response = await chatService.sendMessage(userMsg.text, session.id);
            fullText = response;
            setMessages((prev) =>
              prev.map((m) => (m._id === botMsgId ? { ...m, text: fullText } : m))
            );
            await chatService.addMessage(session.id, {
              role: 'assistant',
              content: fullText,
            });
          } catch (err2: any) {
            setMessages((prev) =>
              prev.map((m) =>
                m._id === botMsgId ? { ...m, text: '抱歉，请求失败，请重试。' } : m
              )
            );
          }
          setLoading(false);
        }
      );
    } catch {
      // Non-streaming fallback
      try {
        const response = await chatService.sendMessage(userMsg.text, session.id);
        fullText = response;
        setMessages((prev) =>
          prev.map((m) => (m._id === botMsgId ? { ...m, text: fullText } : m))
        );
        await chatService.addMessage(session.id, {
          role: 'assistant',
          content: fullText,
        });
      } catch (err: any) {
        setMessages((prev) =>
          prev.map((m) =>
            m._id === botMsgId ? { ...m, text: '抱歉，请求失败，请重试。' } : m
          )
        );
      }
      setLoading(false);
    }
  }, [session]);

  const renderBubble = (props: any) => (
    <Bubble
      {...props}
      wrapperStyle={{
        left: { backgroundColor: COLORS.white, borderWidth: 1, borderColor: COLORS.border },
        right: { backgroundColor: COLORS.primary },
      }}
      textStyle={{
        left: { color: COLORS.text },
        right: { color: COLORS.white },
      }}
    />
  );

  const renderSend = (props: any) => (
    <Send {...props} containerStyle={styles.sendContainer}>
      <View style={styles.sendBtn}>
        <Text style={styles.sendIcon}>➤</Text>
      </View>
    </Send>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={80}
    >
      <View style={styles.topBar}>
        <Text style={styles.topTitle}>AI助手</Text>
        <TouchableOpacity onPress={handleNewChat} style={styles.newChatBtn}>
          <Text style={styles.newChatText}>新对话</Text>
        </TouchableOpacity>
      </View>

      {messages.length === 0 ? (
        <View style={styles.welcome}>
          <View style={styles.welcomeCard}>
            <Text style={styles.welcomeIcon}>🤖</Text>
            <Text style={styles.welcomeTitle}>你好，我是Rogers</Text>
            <Text style={styles.welcomeDesc}>
              你的专业健身和健康管理助手。我可以帮你制定训练计划、管理饮食、追踪健康数据。
            </Text>
            <Text style={styles.promptLabel}>你可以试试问我：</Text>
            {QUICK_PROMPTS.map((prompt, i) => (
              <TouchableOpacity
                key={i}
                style={styles.promptBtn}
                onPress={() => onSend([{ _id: Date.now().toString(), text: prompt, createdAt: new Date(), user: { _id: 1 } }])}
              >
                <Text style={styles.promptText}>{prompt}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ) : (
        <GiftedChat
          messages={messages}
          onSend={onSend}
          user={{ _id: 1 }}
          renderBubble={renderBubble}
          renderSend={renderSend}
          renderInputToolbar={(props) => (
            <InputToolbar
              {...props}
              containerStyle={styles.inputToolbar}
              primaryStyle={{ alignItems: 'center' }}
            />
          )}
          {...({ isLoadingEarlier: loading } as any)}
        />
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 56,
    backgroundColor: COLORS.white,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    paddingHorizontal: 16,
  },
  topTitle: { fontSize: 18, fontWeight: '600', color: COLORS.text, flex: 1, textAlign: 'center' },
  newChatBtn: {
    position: 'absolute',
    right: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: COLORS.primary + '18',
  },
  newChatText: { color: COLORS.primary, fontSize: 14, fontWeight: '500' },
  welcome: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  welcomeCard: {
    backgroundColor: COLORS.white,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 24,
    alignItems: 'center',
    width: '100%',
  },
  welcomeIcon: { fontSize: 48, marginBottom: 12 },
  welcomeTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.text, marginBottom: 8 },
  welcomeDesc: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 20,
  },
  promptLabel: { fontSize: 13, color: COLORS.textSecondary, alignSelf: 'flex-start', marginBottom: 8 },
  promptBtn: {
    backgroundColor: '#E6F7FF',
    borderRadius: 10,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 8,
    width: '100%',
  },
  promptText: { color: COLORS.primary, fontSize: 14, textAlign: 'center' },
  sendContainer: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 4,
    marginBottom: 2,
  },
  sendBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendIcon: { color: COLORS.white, fontSize: 18 },
  inputToolbar: {
    backgroundColor: COLORS.white,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
});
