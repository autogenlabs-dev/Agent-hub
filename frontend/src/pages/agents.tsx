import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { agentsApi } from '@/lib/api';
import type { Agent } from '@/types';
import { getStatusColor } from '@/lib/utils';
import { Activity, Clock, Cpu } from 'lucide-react';

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await agentsApi.list();
      setAgents(data);
    } catch (error) {
      console.error('Error loading agents:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading agents...</div>
      </div>
    );
  }

  const onlineAgents = agents.filter(a => a.status === 'online');
  const offlineAgents = agents.filter(a => a.status !== 'online');

  return (
    <div className="space-y-6">
      <div>
        <h2 data-testid="agents-page-title" className="text-3xl font-bold tracking-tight">Agents</h2>
        <p data-testid="overview-text" className="text-muted-foreground">
          Monitor and manage your connected agents
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card data-testid="total-agents-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div data-testid="total-agents-count" className="text-2xl font-bold">{agents.length}</div>
          </CardContent>
        </Card>

        <Card data-testid="online-agents-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online</CardTitle>
            <div className="h-2 w-2 rounded-full bg-green-500" />
          </CardHeader>
          <CardContent>
            <div data-testid="online-agents-count" className="text-2xl font-bold text-green-500">{onlineAgents.length}</div>
          </CardContent>
        </Card>

        <Card data-testid="offline-agents-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline</CardTitle>
            <div className="h-2 w-2 rounded-full bg-gray-500" />
          </CardHeader>
          <CardContent>
            <div data-testid="offline-agents-count" className="text-2xl font-bold text-gray-500">{offlineAgents.length}</div>
          </CardContent>
        </Card>

        <Card data-testid="agent-types-card">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agent Types</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div data-testid="agent-types-count" className="text-2xl font-bold">
              {new Set(agents.map(a => a.type)).size}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card data-testid="online-agents-section">
          <CardHeader>
            <CardTitle data-testid="online-agents-card-title">Online Agents</CardTitle>
            <CardDescription>
              Agents currently connected and active
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div data-testid="online-agents-list" className="space-y-4">
              {onlineAgents.map((agent) => (
                <div key={agent.id} data-testid="agent-item" className="flex items-start justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold">{agent.name}</h3>
                      <Badge data-testid="status-badge" variant="success">online</Badge>
                      <Badge data-testid="type-badge" variant="outline">{agent.type}</Badge>
                    </div>
                    <div className="flex items-center space-x-2 mt-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>Last seen: {new Date(agent.last_seen).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
              {onlineAgents.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No online agents
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card data-testid="all-agents-section">
          <CardHeader>
            <CardTitle data-testid="all-agents-card-title">All Agents</CardTitle>
            <CardDescription>
              Complete list of all registered agents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div data-testid="all-agents-list" className="space-y-3 max-h-96 overflow-y-auto">
              {agents.map((agent) => (
                <div key={agent.id} data-testid="agent-item" className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent transition-colors">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium">{agent.name}</h3>
                      <Badge data-testid="type-badge" variant="outline">{agent.type}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      ID: {agent.id.slice(0, 8)}...
                    </p>
                  </div>
                  <Badge data-testid="status-badge" className={getStatusColor(agent.status)}>{agent.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}