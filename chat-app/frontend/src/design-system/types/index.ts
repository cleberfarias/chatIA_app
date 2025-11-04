export interface Message {
  id: string;
  author: string;
  text: string;
  timestamp: number;
  status?: 'sent' | 'delivered' | 'read';
  type?: 'text' | 'image' | 'file' | 'audio';
}

export interface User {
  id: string;
  name: string;
  avatar?: string;
  online: boolean;
  lastSeen?: number;
}

export interface ChatRoom {
  id: string;
  name: string;
  participants: User[];
  lastMessage?: Message;
  unreadCount: number;
}