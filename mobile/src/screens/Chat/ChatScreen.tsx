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
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GiftedChat, IMessage, Send, Bubble, InputToolbar } from 'react-native-gifted-chat';
import { chatService } from '../../services/chat';
import { COLORS, SHADOWS } from '../../constants';
import type { ChatSession } from '../../types';

const BOT_USER = { _id: 2, name: 'Rogers' };
const QUICK_PROMPTS = [
  { text: '帮我制定一个减脂训练计划', icon: 'barbell' as keyof typeof Ionicons.glyphMap },
  { text: '今天应该吃多少蛋白质？', icon: 'nutrition' as keyof typeof Ionicons.glyphMap },
  { text: '如何提高跑步耐力？', icon: 'heart' as keyof typeof Ionicons.glyphMap },
];

export default function ChatScreen() {
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState<IMessage[]>([]);
  const [session, setSession] = useState<ChatSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedReasoning, setExpandedReasoning] = useState<Set<string>>(new Set());
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

      const gifted = current.messages.map((m, i) => ({
        _id: `${current.id}-${i}`,
        text: m.content,
        createdAt: new Date(current.createdAt),
        user: m.role === 'user' ? { _id: 1 } : BOT_USER,
        customData: m.reasoning ? { reasoning: m.reasoning } : undefined,
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

    await chatService.addMessage(session.id, {
      role: 'user',
      content: userMsg.text,
    });

    setLoading(true);

    const botMsgId = `${Date.now()}-bot`;
    const botMsg: IMessage = {
      _id: botMsgId,
      text: '',
      createdAt: new Date(),
      user: BOT_USER,
    };
    setMessages((prev) => GiftedChat.append(prev, [botMsg]));

    let fullText = '';
    let fullReasoning = '';

    try {
      await chatService.sendMessageStream(
        userMsg.text,
        session.id,
        (chunk) => {
          fullText += chunk;
          isStreaming.current = true;
          setMessages((prev) =>
            prev.map((m) => (m._id === botMsgId ? {
              ...m,
              text: fullText,
              customData: { reasoning: fullReasoning }
            } : m))
          );
        },
        (reasoningChunk) => {
          fullReasoning += reasoningChunk;
          isStreaming.current = true;
          setMessages((prev) =>
            prev.map((m) => (m._id === botMsgId ? {
              ...m,
              text: fullText,
              customData: { reasoning: fullReasoning }
            } : m))
          );
        },
        async () => {
          isStreaming.current = false;
          await chatService.addMessage(session.id, {
            role: 'assistant',
            content: fullText,
            reasoning: fullReasoning,
          });
          setLoading(false);
        },
        async () => {
          isStreaming.current = false;
          try {
            const response = await chatService.sendMessage(userMsg.text, session.id);
            fullText = response.reply;
            fullReasoning = response.reasoning;
            setMessages((prev) =>
              prev.map((m) => (m._id === botMsgId ? {
                ...m,
                text: fullText,
                customData: { reasoning: fullReasoning }
              } : m))
            );
            await chatService.addMessage(session.id, {
              role: 'assistant',
              content: fullText,
              reasoning: fullReasoning,
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
      try {
        const response = await chatService.sendMessage(userMsg.text, session.id);
        fullText = response.reply;
        fullReasoning = response.reasoning;
        setMessages((prev) =>
          prev.map((m) => (m._id === botMsgId ? {
            ...m,
            text: fullText,
            customData: { reasoning: fullReasoning }
          } : m))
        );
        await chatService.addMessage(session.id, {
          role: 'assistant',
          content: fullText,
          reasoning: fullReasoning,
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

  const renderBubble = (props: any) => {
    const reasoning = props.currentMessage?.customData?.reasoning;
    const hasReasoning = reasoning && reasoning.trim().length > 0;
    const messageId = props.currentMessage?._id;
    const isExpanded = messageId && expandedReasoning.has(messageId);

    const toggleReasoning = () => {
      if (messageId) {
        setExpandedReasoning(prev => {
          const next = new Set(prev);
          if (next.has(messageId)) {
            next.delete(messageId);
          } else {
            next.add(messageId);
          }
          return next;
        });
      }
    };

    return (
      <View>
        {hasReasoning && (
          <View style={styles.reasoningContainer}>
            <TouchableOpacity style={styles.reasoningHeader} onPress={toggleReasoning} activeOpacity={0.7}>
              <Ionicons name="bulb-outline" size={14} color={COLORS.textSecondary} />
              <Text style={styles.reasoningTitle}>思考过程</Text>
              <Ionicons
                name={isExpanded ? "chevron-up" : "chevron-down"}
                size={14}
                color={COLORS.textSecondary}
              />
            </TouchableOpacity>
            {isExpanded && (
              <Text style={styles.reasoningText}>{reasoning}</Text>
            )}
          </View>
        )}
        <Bubble
          {...props}
          wrapperStyle={{
            left: {
              backgroundColor: COLORS.white,
              borderWidth: 0,
              ...SHADOWS.small,
              marginLeft: 4,
              maxWidth: '80%',
            },
            right: {
              backgroundColor: COLORS.primary,
              maxWidth: '80%',
            },
          }}
          textStyle={{
            left: {
              color: COLORS.text,
              fontSize: 15,
              lineHeight: 22,
            },
            right: {
              color: COLORS.white,
              fontSize: 15,
              lineHeight: 22,
            },
          }}
          timeTextStyle={{
            left: { color: COLORS.textTertiary },
            right: { color: 'rgba(255,255,255,0.7)' },
          }}
        />
      </View>
    );
  };

  const renderSend = (props: any) => (
    <Send {...props} containerStyle={styles.sendContainer}>
      <LinearGradient
        colors={[COLORS.gradientStart, COLORS.gradientEnd]}
        style={styles.sendBtn}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <Ionicons name="send" size={18} color={COLORS.white} />
      </LinearGradient>
    </Send>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={80}
    >
      <View style={[styles.topBar, { paddingTop: insets.top + 6 }]}>
        <View style={styles.topBarContent}>
          <View style={styles.botAvatar}>
            <Ionicons name="sparkles" size={18} color={COLORS.primary} />
          </View>
          <Text style={styles.topTitle}>AI 健身助手</Text>
          <TouchableOpacity onPress={handleNewChat} style={styles.newChatBtn}>
            <Ionicons name="add" size={20} color={COLORS.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {messages.length === 0 ? (
        <View style={styles.welcome}>
          <View style={styles.welcomeCard}>
            <LinearGradient
              colors={[COLORS.gradientStart, COLORS.gradientEnd]}
              style={styles.welcomeIcon}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Ionicons name="fitness" size={36} color={COLORS.white} />
            </LinearGradient>
            <Text style={styles.welcomeTitle}>你好，我是 Rogers</Text>
            <Text style={styles.welcomeDesc}>
              你的专业健身和健康管理助手。我可以帮你制定训练计划、管理饮食、追踪健康数据。
            </Text>
            <Text style={styles.promptLabel}>你可以试试问我：</Text>
            {QUICK_PROMPTS.map((prompt, i) => (
              <TouchableOpacity
                key={i}
                style={styles.promptBtn}
                onPress={() => onSend([{ _id: Date.now().toString(), text: prompt.text, createdAt: new Date(), user: { _id: 1 } }])}
                activeOpacity={0.7}
              >
                <View style={styles.promptIconWrap}>
                  <Ionicons name={prompt.icon} size={16} color={COLORS.primary} />
                </View>
                <Text style={styles.promptText}>{prompt.text}</Text>
                <Ionicons name="chevron-forward" size={16} color={COLORS.textTertiary} />
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
          renderAvatarOnTop
          showUserAvatar={false}
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
    paddingBottom: 10,
    paddingHorizontal: 16,
    backgroundColor: COLORS.white,
  },
  topBarContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  botAvatar: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.blueBg,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
  },
  topTitle: { fontSize: 16, fontWeight: '700', color: COLORS.text, flex: 1 },
  newChatBtn: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.blueBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  welcome: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  welcomeCard: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 28,
    alignItems: 'center',
    width: '100%',
    ...SHADOWS.card,
  },
  welcomeIcon: {
    width: 72,
    height: 72,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  welcomeTitle: { fontSize: 22, fontWeight: 'bold', color: COLORS.text, marginBottom: 8 },
  welcomeDesc: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  promptLabel: { fontSize: 13, color: COLORS.textSecondary, alignSelf: 'flex-start', marginBottom: 10, fontWeight: '500' },
  promptBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.background,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 14,
    marginBottom: 8,
    width: '100%',
    gap: 10,
  },
  promptIconWrap: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.blueBg,
    justifyContent: 'center',
    alignItems: 'center',
  },
  promptText: { color: COLORS.text, fontSize: 14, flex: 1 },
  sendContainer: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 4,
    marginBottom: 2,
  },
  sendBtn: {
    width: 38,
    height: 38,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  inputToolbar: {
    backgroundColor: COLORS.white,
    borderTopWidth: 0,
    ...SHADOWS.small,
  },
  reasoningContainer: {
    marginLeft: 8,
    marginRight: 60,
    marginBottom: 4,
    backgroundColor: 'rgba(159, 166, 177, 0.1)',
    borderRadius: 12,
    padding: 12,
    maxWidth: '80%',
  },
  reasoningHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  reasoningTitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    fontWeight: '500',
    flex: 1,
  },
  reasoningText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 18,
    marginTop: 8,
  },
});
