import React from 'react'
import ReactDOM from 'react-dom/client'
import { App as AntdApp } from 'antd'
import './styles/global.css'
import App from './App'

// Suppress forwardRef warning from @agentscope-ai/chat library
const originalError = console.error
console.error = (...args: any[]) => {
  const msg = typeof args[0] === 'string' ? args[0] : ''
  if (msg.includes('forwardRef render functions accept exactly two parameters')) return
  originalError.apply(console, args)
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AntdApp>
      <App />
    </AntdApp>
  </React.StrictMode>
)