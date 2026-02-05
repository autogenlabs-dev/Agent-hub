import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { messagesApi, agentsApi } from '@/lib/api';
import type { Message, Agent } from '@/types';
import { formatDate } from '@/lib/utils';
import { MessageSquare, User } from 'lucide-react';

export default function Messages() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [messagesData, agentsData] = await Promise.all([
        messagesApi.getRecent(48),
        agentsApi.list(),
      ]);
      setMessages(messagesData);
      setAgents(agentsData);
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAgentName = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent?.name || 'Unknown Agent';
  };

  const getAgentType = (agentId: string) => {
    const agent = agents.find(a => a.id === agentId);
    return agent?.type || 'unknown';
  };

  const groupedMessages = messages.reduce((acc, message) => {
    const date = new Date(message.created_at).toLocaleDateString();
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(message);
    return acc;
  }, {} as Record<string, Message[]>);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading messages...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 data-testid="messages-page-title" className="text-3xl font-bold tracking-tight">Messages</h2>
        <p data-testid="overview-text" className="text-muted-foreground">
          Communication history between agents
        </p>
      </div>

      {Object.entries(groupedMessages).map(([date, dayMessages]) => (
        <div key={date} className="space-y-4">
          <h3 className="text-lg font-semibold text-muted-foreground">{date}</h3>
          <div data-testid="messages-list" className="space-y-3">
            {dayMessages.map((message) => (
              <Card key={message.id} data-testid="message-item">
                <CardContent className="pt-6">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center">
                        <User className="h-5 w-5 text-primary-foreground" />
                      </div>
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 data-testid="message-sender" className="font-semibold">{getAgentName(message.sender_id)}</h4>
                          <p className="text-sm text-muted-foreground">
                            {getAgentType(message.sender_id)}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">{message.message_type}</Badge>
                          <span data-testid="message-timestamp" className="text-sm text-muted-foreground">
                            {formatDate(message.created_at)}
                          </span>
                        </div>
                      </div>
                      <div data-testid="message-content" className="p-3 bg-muted rounded-lg">
                        <p className="text-sm">{message.content}</p>
                      </div>
                      {message.task_id && (
                        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                          <MessageSquare className="h-4 w-4" />
                          <span>Related to task: {message.task_id.slice(0, 8)}...</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}

      {messages.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No messages yet</p>
            <p className="text-sm text-muted-foreground mt-2">
              Messages will appear here when agents communicate
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}