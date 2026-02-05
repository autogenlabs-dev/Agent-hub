import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { tasksApi } from '@/lib/api';
import type { Task } from '@/types';
import { getStatusColor, getPriorityColor, getPriorityLabel, formatDate } from '@/lib/utils';
import { CheckSquare, Clock, AlertTriangle } from 'lucide-react';

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'in_progress' | 'completed'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      let data;
      if (filter === 'pending') {
        data = await tasksApi.getPending();
      } else if (filter === 'in_progress') {
        data = await tasksApi.list({ status: 'in_progress' });
      } else if (filter === 'completed') {
        data = await tasksApi.list({ status: 'completed' });
      } else {
        data = await tasksApi.list();
      }
      setTasks(data);
    } catch (error) {
      console.error('Error loading tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (taskId: string) => {
    try {
      await tasksApi.update(taskId, { status: 'completed' });
      loadTasks();
    } catch (error) {
      console.error('Error completing task:', error);
    }
  };

  const filteredTasks = tasks;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 data-testid="tasks-page-title" className="text-3xl font-bold tracking-tight">Tasks</h2>
          <p data-testid="overview-text" className="text-muted-foreground">
            Manage and track agent tasks
          </p>
        </div>
        <Button>Create Task</Button>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          onClick={() => setFilter('all')}
        >
          All
        </Button>
        <Button
          variant={filter === 'pending' ? 'default' : 'outline'}
          onClick={() => setFilter('pending')}
        >
          Pending
        </Button>
        <Button
          variant={filter === 'in_progress' ? 'default' : 'outline'}
          onClick={() => setFilter('in_progress')}
        >
          In Progress
        </Button>
        <Button
          variant={filter === 'completed' ? 'default' : 'outline'}
          onClick={() => setFilter('completed')}
        >
          Completed
        </Button>
      </div>

      {/* Task List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading tasks...</div>
        </div>
      ) : (
        <div data-testid="tasks-list" className="grid gap-4">
          {filteredTasks.map((task) => (
            <Card key={task.id} data-testid="task-item">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{task.title}</CardTitle>
                    <CardDescription className="mt-1">
                      {task.description || 'No description'}
                    </CardDescription>
                  </div>
                  <Badge data-testid="priority-badge" className={getPriorityColor(task.priority)}>
                    {getPriorityLabel(task.priority)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2 text-sm">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">
                        Created {formatDate(task.created_at)}
                      </span>
                    </div>
                    {task.due_date && (
                      <div className="flex items-center space-x-2 text-sm">
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">
                          Due {formatDate(task.due_date)}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge data-testid="status-badge" className={getStatusColor(task.status)}>{task.status}</Badge>
                    {task.status !== 'completed' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleComplete(task.id)}
                      >
                        <CheckSquare className="h-4 w-4 mr-2" />
                        Complete
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          {filteredTasks.length === 0 && (
            <div className="col-span-full text-center py-12 text-muted-foreground">
              No tasks found
            </div>
          )}
        </div>
      )}
    </div>
  );
}