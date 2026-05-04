import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles/global.css'
import App from './App'

// Suppress forwardRef warning from @agentscope-ai/chat library
const originalError = console.error
console.error = (...args) => {
  if (args[0]?.includes?.('forwardRef render functions accept exactly two parameters')) {
    return
  }
  originalError.apply(console, args)
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)