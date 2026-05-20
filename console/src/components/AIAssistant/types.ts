export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: any;
  response?: any;
  status: 'generating' | 'finished' | 'error' | 'interrupted';
  createdAt: number;
}
