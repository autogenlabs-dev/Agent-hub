import axios from 'axios';
import type { Agent, Message, Task, TaskAssignment, SharedMemory } from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Agents
export const agentsApi = {
  list: async () => {
    const response = await api.get<Agent[]>('/agents');
    return response.data;
  },
  getOnline: async () => {
    const response = await api.get<Agent[]>('/agents/online');
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get<Agent>(`/agents/${id}`);
    return response.data;
  },
  updateStatus: async (id: string, status: string) => {
    const response = await api.put<Agent>(`/agents/${id}/status`, { status });
    return response.data;
  },
};

// Messages
export const messagesApi = {
  list: async (params?: { sender_id?: string; task_id?: string; since?: string }) => {
    const response = await api.get<Message[]>('/messages', { params });
    return response.data;
  },
  getRecent: async (hours: number = 24) => {
    const response = await api.get<Message[]>('/messages/recent', { params: { hours } });
    return response.data;
  },
  getByTask: async (taskId: string) => {
    const response = await api.get<Message[]>(`/messages/task/${taskId}`);
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get<Message>(`/messages/${id}`);
    return response.data;
  },
};

// Tasks
export const tasksApi = {
  list: async (params?: { status?: string; priority?: number }) => {
    const response = await api.get<Task[]>('/tasks', { params });
    return response.data;
  },
  getPending: async () => {
    const response = await api.get<Task[]>('/tasks/pending');
    return response.data;
  },
  getOverdue: async () => {
    const response = await api.get<Task[]>('/tasks/overdue');
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get<Task>(`/tasks/${id}`);
    return response.data;
  },
  create: async (data: {
    creator_id: string;
    title: string;
    description?: string;
    priority?: number;
    due_date?: string;
    requirements?: Record<string, any>;
  }) => {
    const response = await api.post<Task>('/tasks', data);
    return response.data;
  },
  update: async (id: string, data: Partial<Task>) => {
    const response = await api.put<Task>(`/tasks/${id}`, data);
    return response.data;
  },
  assign: async (taskId: string, agentId: string) => {
    const response = await api.post<TaskAssignment>(`/tasks/${taskId}/assign`, {
      agent_id: agentId,
    });
    return response.data;
  },
  complete: async (taskId: string, agentId: string, result?: Record<string, any>) => {
    const response = await api.post<Task>(
      `/tasks/${taskId}/complete`,
      { result },
      { params: { agent_id: agentId } }
    );
    return response.data;
  },
  getAssignments: async (taskId: string) => {
    const response = await api.get<TaskAssignment[]>(`/tasks/${taskId}/assignments`);
    return response.data;
  },
  getByAgent: async (agentId: string, status?: string) => {
    const response = await api.get<Task[]>(`/tasks/agent/${agentId}`, {
      params: status ? { status } : undefined,
    });
    return response.data;
  },
};

// Memory
export const memoryApi = {
  list: async (params?: { created_by?: string }) => {
    const response = await api.get<SharedMemory[]>('/memory', { params });
    return response.data;
  },
  getByKey: async (key: string) => {
    const response = await api.get<SharedMemory>(`/memory/key/${key}`);
    return response.data;
  },
  getById: async (id: string) => {
    const response = await api.get<SharedMemory>(`/memory/${id}`);
    return response.data;
  },
  create: async (data: {
    key: string;
    value: Record<string, any>;
    created_by: string;
    access_control?: Record<string, string[]>;
  }) => {
    const response = await api.post<SharedMemory>('/memory', data);
    return response.data;
  },
  updateByKey: async (key: string, value: Record<string, any>) => {
    const response = await api.put<SharedMemory>(`/memory/key/${key}`, { value });
    return response.data;
  },
  deleteByKey: async (key: string) => {
    await api.delete(`/memory/key/${key}`);
  },
};

export default api;