import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (seconds < 60) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  
  return date.toLocaleDateString();
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'online':
    case 'completed':
      return 'text-green-500';
    case 'offline':
    case 'failed':
      return 'text-gray-500';
    case 'busy':
    case 'in_progress':
      return 'text-yellow-500';
    case 'error':
      return 'text-red-500';
    case 'pending':
      return 'text-blue-500';
    case 'assigned':
      return 'text-purple-500';
    default:
      return 'text-gray-500';
  }
}

export function getPriorityColor(priority: number): string {
  switch (priority) {
    case 1:
      return 'bg-blue-100 text-blue-800';
    case 2:
      return 'bg-yellow-100 text-yellow-800';
    case 3:
      return 'bg-orange-100 text-orange-800';
    case 4:
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export function getPriorityLabel(priority: number): string {
  switch (priority) {
    case 1:
      return 'Low';
    case 2:
      return 'Medium';
    case 3:
      return 'High';
    case 4:
      return 'Urgent';
    default:
      return 'Unknown';
  }
}