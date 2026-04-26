import { useState, useCallback } from 'react';
import WelcomeScreen from './components/WelcomeScreen';
import ChatScreen from './components/ChatScreen';
import './index.css';

function App() {
  const [inChat, setInChat] = useState(false);

  const handleStartChat = useCallback(() => {
    setInChat(true);
  }, []);

  const handleNewChat = useCallback(() => {
    setInChat(false);
    setTimeout(() => setInChat(true), 50);
  }, []);

  if (!inChat) {
    return <WelcomeScreen onStart={handleStartChat} />;
  }

  return <ChatScreen onNewChat={handleNewChat} />;
}

export default App;
