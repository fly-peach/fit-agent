import { AgentScopeRuntimeWebUI, IAgentScopeRuntimeWebUIOptions } from '@agentscope-ai/chat'
import { ConfigProvider } from 'antd'
import { useMemo } from 'react'
import sessionApi from './sessionApi'
import ChatActionGroup from './components/ChatActionGroup'
import ChatHeaderTitle from './components/ChatHeaderTitle'
import './components/ChatSessionDrawer/index.css'
import './components/ChatSearchPanel/index.css'
import './components/ChatSessionItem/index.css'
import './components/ChatHeaderTitle/index.css'
import './index.css'

const AIAssistant: React.FC = () => {

  const options = useMemo(() => {
    const token = localStorage.getItem('token')
    return {
      api: {
        baseURL: BASE_URL,
        token: token || '',
      },
      session: {
        multiple: true,
        api: sessionApi,
        hideBuiltInSessionList: true,
      },
      theme: {
        colorPrimary: '#615CED',
        darkMode: false,
        prefix: 'agentscope-runtime-webui',
        rightHeader: <ChatActionGroup />,
        leftHeader: <ChatHeaderTitle />,
      },
      sender: {
        attachments: {
          customRequest: async ({ file, onSuccess, onError }: any) => {
            const formData = new FormData()
            formData.append('file', file)
            const token = localStorage.getItem('token')
            try {
              const resp = await fetch('/api/agent/upload', {
                method: 'POST',
                headers: { Authorization: `Bearer ${token}` },
                body: formData,
              })
              if (!resp.ok) throw new Error('Upload failed')
              const data = await resp.json()
              onSuccess({ url: data.url })
            } catch (e: any) {
              onError(e)
            }
          },
        },
        maxLength: 10000,
      },
      welcome: {
        greeting: '你好，我是你的健身助手！',
        description: '我可以帮你制定训练计划、管理饮食、追踪健康数据。',
        avatar: 'https://images.icon-icons.com/1429/PNG/96/icon-robots-3_98540.png',
        prompts: [
          { value: '帮我制定一个减脂训练计划' },
          { value: '今天应该吃多少蛋白质？' },
          { value: '如何提高跑步耐力？' },
        ],
      },
    } as unknown as IAgentScopeRuntimeWebUIOptions
  }, [])

  return (
    <ConfigProvider getPopupContainer={() => document.querySelector('.agentscope-runtime-webui') as HTMLElement}>
      <div className="agentscope-runtime-webui">
        <AgentScopeRuntimeWebUI options={options} />
      </div>
    </ConfigProvider>
  )
}

export default AIAssistant
