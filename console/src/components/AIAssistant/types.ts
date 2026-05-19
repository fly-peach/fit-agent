export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: any;
  response?: any;
  status: 'loading' | 'finished' | 'error';
  createdAt: number;
}
