export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  created_at: string;
  last_seen: string;
  metadata: Record<string, any>;
}

export interface Message {
  id: string;
  sender_id: string;
  content: string;
  message_type: 'text' | 'system' | 'error' | 'info';
  task_id?: string;
  created_at: string;
  metadata: Record<string, any>;
}

export interface Task {
  id: string;
  creator_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'failed';
  priority: 1 | 2 | 3 | 4;
  created_at: string;
  due_date?: string;
  completed_at?: string;
  requirements: Record<string, any>;
}

export interface TaskAssignment {
  id: string;
  task_id: string;
  agent_id: string;
  status: 'assigned' | 'accepted' | 'rejected' | 'completed' | 'failed';
  assigned_at: string;
  completed_at?: string;
}

export interface SharedMemory {
  id: string;
  key: string;
  value: Record<string, any>;
  created_by: string;
  created_at: string;
  updated_at: string;
  access_control?: Record<string, string[]>;
}

export interface WSEvent {
  event: string;
  data: any;
}