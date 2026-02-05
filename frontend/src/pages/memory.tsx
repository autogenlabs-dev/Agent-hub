import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { memoryApi, agentsApi } from '@/lib/api';
import type { SharedMemory, Agent } from '@/types';
import { formatDate } from '@/lib/utils';
import { Database, Plus, Trash2, Edit } from 'lucide-react';

export default function Memory() {
  const [memories, setMemories] = useState<SharedMemory[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMemory, setSelectedMemory] = useState<SharedMemory | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [memoriesData, agentsData] = await Promise.all([
        memoryApi.list(),
        agentsApi.list(),
      ]);
      setMemories(memoriesData);
      setAgents(agentsData);
    } catch (error) {
      console.error('Error loading memory:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent?.name || 'Unknown Agent';
  };

  const handleDelete = async (key: string) => {
    if (confirm('Are you sure you want to delete this memory?')) {
      try {
        await memoryApi.deleteByKey(key);
        setMemories(memories.filter(m => m.key !== key));
      } catch (error) {
        console.error('Error deleting memory:', error);
      }
    }
  };

  const handleView = (memory: SharedMemory) => {
    setSelectedMemory(memory);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading memory...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 data-testid="memory-page-title" className="text-3xl font-bold tracking-tight">Shared Memory</h2>
          <p data-testid="overview-text" className="text-muted-foreground">
            Key-value store for agent data sharing
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Memory
        </Button>
      </div>

      {/* Memory Grid */}
      <div data-testid="entries-list" className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {memories.map((memory) => (
          <Card key={memory.id} data-testid="memory-item">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle data-testid="entry-key" className="text-lg truncate">{memory.key}</CardTitle>
                  <CardDescription className="mt-1">
                    Created by {getAgentName(memory.created_by)}
                  </CardDescription>
                </div>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => handleView(memory)}
                >
                  <Edit className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-1">Value</p>
                  <div data-testid="entry-value" className="p-3 bg-muted rounded-lg max-h-32 overflow-y-auto">
                    <pre className="text-xs">
                      {JSON.stringify(memory.value, null, 2)}
                    </pre>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <div className="flex items-center space-x-2">
                    <span>Updated {formatDate(memory.updated_at)}</span>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => handleDelete(memory.key)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {memories.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No shared memory yet</p>
            <p className="text-sm text-muted-foreground mt-2">
              Agents can store and share data here
            </p>
          </CardContent>
        </Card>
      )}

      {/* Memory Detail Modal */}
      {selectedMemory && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle>{selectedMemory.key}</CardTitle>
                  <CardDescription>
                    Created by {getAgentName(selectedMemory.created_by)} on{' '}
                    {formatDate(selectedMemory.created_at)}
                  </CardDescription>
                </div>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => setSelectedMemory(null)}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">Value</p>
                  <div className="p-4 bg-muted rounded-lg overflow-x-auto">
                    <pre className="text-sm">
                      {JSON.stringify(selectedMemory.value, null, 2)}
                    </pre>
                  </div>
                </div>
                {selectedMemory.access_control && (
                  <div>
                    <p className="text-sm font-medium mb-2">Access Control</p>
                    <div className="space-y-2">
                      {Object.entries(selectedMemory.access_control).map(([accessType, agentIds]) => (
                        <div key={accessType} className="flex items-center justify-between p-2 border rounded-lg">
                          <span className="font-medium capitalize">{accessType}</span>
                          <div className="flex gap-1">
                            {agentIds.map((agentId) => (
                              <Badge key={agentId} variant="outline">
                                {getAgentName(agentId)}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}