import { AgentScopeRuntimeWebUI, IAgentScopeRuntimeWebUIOptions } from '@agentscope-ai/chat';
import ChatActionGroup from './components/ChatActionGroup';
import ChatHeaderTitle from './components/ChatHeaderTitle';
import { useMemo } from 'react';
import sessionApi from './sessionApi';
import { useLocalStorageState } from 'ahooks';
import defaultConfig from './OptionsPanel/defaultConfig';
import Weather from '../Cards/Weather';

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
      customToolRenderConfig: {
        'weather search mock': Weather,
      },
    } as unknown as IAgentScopeRuntimeWebUIOptions
  }, [optionsConfig]);

  return <div style={{ height: '100vh' }}>
    <AgentScopeRuntimeWebUI
      options={options}
    />
  </div>;
}