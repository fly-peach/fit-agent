import { AgentScopeRuntimeWebUI, IAgentScopeRuntimeWebUIOptions } from '@agentscope-ai/chat'
import { ConfigProvider } from 'antd'
import { useEffect, useMemo, useRef } from 'react'
import sessionApi from './sessionApi'
import ChatActionGroup from './components/ChatActionGroup'
import ChatHeaderTitle from './components/ChatHeaderTitle'
import './components/ChatSessionDrawer/index.css'
import './components/ChatSearchPanel/index.css'
import './components/ChatSessionItem/index.css'
import './components/ChatHeaderTitle/index.css'
import './index.css'

const AIAssistant: React.FC = () => {
  const originalFetchRef = useRef<Window['fetch'] | null>(null)

  // 拦截 fetch，为 /process 请求注入 Authorization header
  useEffect(() => {
    const originalFetch = window.fetch
    originalFetchRef.current = originalFetch

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url
      if (url.includes('/process')) {
        const token = localStorage.getItem('token')
        if (token) {
          const headers = new Headers(init?.headers || {})
          headers.set('Authorization', `Bearer ${token}`)
          init = { ...init, headers }
        }
      }
      return originalFetch.call(window, input, init)
    }

    return () => {
      window.fetch = originalFetchRef.current || originalFetch
    }
  }, [])

  const options = useMemo(() => {
    return {
      api: {
        baseURL: BASE_URL,
        requestInterceptors: [
          (config: Record<string, any>) => {
            const token = localStorage.getItem('token')
            if (token) {
              config.headers = {
                ...(config.headers || {}),
                Authorization: `Bearer ${token}`,
              }
            }
            return config
          },
        ],
      },
      session: {
        multiple: true,
        api: sessionApi,
        hideBuiltInSessionList: true,
      },
      theme: {
        colorPrimary: '#0EA5E9',
        darkMode: false,
        prefix: 'fitagent-chat',
        rightHeader: <ChatActionGroup />,
        leftHeader: <ChatHeaderTitle />,
      },
      sender: {
        attachments: false,
        maxLength: 2000,
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
    <ConfigProvider getPopupContainer={() => document.querySelector('.fitagent-chat') as HTMLElement}>
      <div className="fitagent-chat">
        <AgentScopeRuntimeWebUI options={options} />
      </div>
    </ConfigProvider>
  )
}

export default AIAssistant
