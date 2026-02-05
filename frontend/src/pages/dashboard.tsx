import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { agentsApi, tasksApi, messagesApi } from '@/lib/api';
import type { Agent, Task, Message } from '@/types';
import { Activity, CheckSquare, MessageSquare, Clock } from 'lucide-react';

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsData, tasksData, messagesData] = await Promise.all([
        agentsApi.list(),
        tasksApi.list(),
        messagesApi.getRecent(24),
      ]);
      setAgents(agentsData);
      setTasks(tasksData);
      setMessages(messagesData);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const onlineAgents = agents.filter(a => a.status === 'online');
  const completedTasks = tasks.filter(t => t.status === 'completed');
  const pendingTasks = tasks.filter(t => t.status === 'pending' || t.status === 'assigned');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 data-testid="dashboard-title" className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of your agent communication channel
        </p>
      </div>

      {/* Stats Cards */}
      <div data-testid="stats-cards" className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card data-testid="online-agents-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online Agents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div data-testid="online-agents-count" className="text-2xl font-bold">{onlineAgents.length}</div>
            <p className="text-xs text-muted-foreground">
              out of {agents.length} total
            </p>
          </CardContent>
        </Card>

        <Card data-testid="pending-tasks-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Tasks</CardTitle>
            <CheckSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div data-testid="pending-tasks-count" className="text-2xl font-bold">{pendingTasks.length}</div>
            <p className="text-xs text-muted-foreground">
              {completedTasks.length} completed today
            </p>
          </CardContent>
        </Card>

        <Card data-testid="recent-messages-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div data-testid="recent-messages-count" className="text-2xl font-bold">{messages.length}</div>
            <p className="text-xs text-muted-foreground">
              last 24 hours
            </p>
          </CardContent>
        </Card>

        <Card data-testid="system-status-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div data-testid="system-status" className="text-2xl font-bold text-green-500">Active</div>
            <p className="text-xs text-muted-foreground">
              All systems operational
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card data-testid="recent-agents-section">
          <CardHeader>
            <CardTitle data-testid="recent-agents-title">Recent Agents</CardTitle>
            <CardDescription>
              Agents that have recently joined or updated their status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div data-testid="recent-agents-list" className="space-y-4">
              {agents.slice(0, 5).map((agent) => (
                <div key={agent.id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{agent.name}</p>
                    <p className="text-sm text-muted-foreground">{agent.type}</p>
                  </div>
                  <Badge variant={agent.status === 'online' ? 'success' : 'secondary'}>
                    {agent.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card data-testid="recent-tasks-section">
          <CardHeader>
            <CardTitle data-testid="recent-tasks-title">Recent Tasks</CardTitle>
            <CardDescription>
              Latest tasks created or updated
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div data-testid="recent-tasks-list" className="space-y-4">
              {tasks.slice(0, 5).map((task) => (
                <div key={task.id} className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium">{task.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {task.description || 'No description'}
                    </p>
                  </div>
                  <Badge variant="outline">{task.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}