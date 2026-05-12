import { AgentScopeRuntimeWebUI, IAgentScopeRuntimeWebUIOptions, Accordion, DefaultCards } from '@agentscope-ai/chat';
import ChatActionGroup from './components/ChatActionGroup';
import ChatHeaderTitle from './components/ChatHeaderTitle';
import { useMemo } from 'react';
import sessionApi from './sessionApi';
import { useLocalStorageState } from 'ahooks';
import defaultConfig from './OptionsPanel/defaultConfig';
import { createStyles } from 'antd-style';
import { Cog, User } from 'lucide-react';

const useStyles = createStyles(({ token, css }) => ({
  content: css`
    white-space: pre-wrap;
    line-height: 1.6;
  `,
}));

// 自定义 Text 卡片组件
const CustomTextCard = (props: any) => {
  const { styles } = useStyles();

  const text = props.data?.content?.[0]?.text || '';

  // 检查是否是分析员 B 的消息
  if (text.includes('---ANALYST_B_START---')) {
    const content = text
      .replace('---ANALYST_B_START---', '')
      .replace('---ANALYST_B_END---', '')
      .trim();

    return (
      <Accordion
        defaultOpen={true}
        title={
          <span style={{ display: 'flex', alignItems: 'center' }}>
            <Cog style={{ marginRight: 8 }} size={18} />
            <strong>技术/逻辑分析</strong>
          </span>
        }
      >
        <div className={styles.content}>{content}</div>
      </Accordion>
    );
  }

  // 检查是否是分析员 C 的消息
  if (text.includes('---ANALYST_C_START---')) {
    const content = text
      .replace('---ANALYST_C_START---', '')
      .replace('---ANALYST_C_END---', '')
      .trim();

    return (
      <Accordion
        defaultOpen={true}
        title={
          <span style={{ display: 'flex', alignItems: 'center' }}>
            <User style={{ marginRight: 8 }} size={18} />
            <strong>用户体验/实践分析</strong>
          </span>
        }
      >
        <div className={styles.content}>{content}</div>
      </Accordion>
    );
  }

  // 其他情况使用默认的 Text 卡片
  return <DefaultCards.Text {...props} />;
};

export default function () {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [optionsConfig, _setOptionsConfig] = useLocalStorageState('agent-scope-runtime-webui-options', {
    defaultValue: defaultConfig,
    listenStorageChange: true,
  });

  const options = useMemo(() => {
    return {
      ...optionsConfig,
      session: {
        multiple: true,
        api: sessionApi,
        hideBuiltInSessionList: true,
      },
      theme: {
        ...optionsConfig.theme,
        rightHeader: <ChatActionGroup />,
        leftHeader: <ChatHeaderTitle />,
      },
      cards: {
        Text: CustomTextCard,
      },
    } as unknown as IAgentScopeRuntimeWebUIOptions;
  }, [optionsConfig]);

  return <div style={{ height: '100vh' }}>
    <AgentScopeRuntimeWebUI
      options={options}
    />
  </div>;
}
