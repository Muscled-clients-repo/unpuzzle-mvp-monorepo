/**
 * WebSocket Provider - Manages global WebSocket connection and integrates with Zustand store
 */
'use client';

import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useWebSocketSSE, WebSocketMessage, WebSocketStatus } from '@/hooks/useWebSocketSSE';
import { useAppStore } from '@/stores/app-store';
import { toast } from 'sonner';

interface WebSocketContextValue {
  status: WebSocketStatus;
  lastMessage: WebSocketMessage | null;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const { 
    setWsStatus,
    handleConfusionEvent,
    handleAnalyticsUpdate,
    handleStudentProgress,
    handleEnrollmentUpdate,
    handleNotification,
    addWebSocketEvent,
  } = useAppStore();

  const { status, lastMessage } = useWebSocketSSE({
    autoConnect: true,
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
    onMessage: (message: WebSocketMessage) => {
      // Add to event log
      addWebSocketEvent({
        type: message.type,
        data: message.data,
        timestamp: message.timestamp || new Date().toISOString()
      });

      // Route message to appropriate handler
      switch (message.type) {
        case 'confusion':
        case 'new_confusion':
          handleConfusionEvent(message.data);
          toast.error(`New confusion from ${message.data?.student_name}`, {
            description: message.data?.message?.substring(0, 100) + '...',
            action: {
              label: 'View',
              onClick: () => {
                // Navigate to confusion or open modal
                console.log('Navigate to confusion:', message.data);
              }
            }
          });
          break;

        case 'course_analytics':
          handleAnalyticsUpdate(message.data);
          break;

        case 'student_progress':
          handleStudentProgress(message.data);
          break;

        case 'enrollment':
        case 'enrollment_update':
          handleEnrollmentUpdate(message.data);
          if (message.data?.action === 'new_enrollment') {
            toast.success('New student enrolled!', {
              description: `${message.data.student?.name} enrolled in your course`
            });
          }
          break;

        case 'notification':
          handleNotification(message);
          // Show notification based on level
          const { message: notificationMessage, level = 'info' } = message;
          if (level === 'error') {
            toast.error(notificationMessage);
          } else if (level === 'warning') {
            toast.warning(notificationMessage);
          } else if (level === 'success') {
            toast.success(notificationMessage);
          } else {
            toast.info(notificationMessage);
          }
          break;

        case 'payment':
        case 'payment_update':
          toast.success('Payment received!', {
            description: `$${message.data?.amount} from ${message.data?.student_name}`,
          });
          break;

        case 'lesson_analytics':
          // Handle lesson analytics updates
          console.log('Lesson analytics update:', message.data);
          break;

        case 'broadcast':
          toast.info(message.message, {
            description: 'System announcement'
          });
          break;

        case 'connected':
          console.log('WebSocket connected successfully');
          break;

        default:
          console.log('Unknown WebSocket message type:', message.type, message);
      }
    },
    onStatusChange: (status: WebSocketStatus) => {
      setWsStatus(status);
      
      // Show connection status changes
      if (status === 'connected') {
        toast.success('Connected to real-time updates');
      } else if (status === 'disconnected') {
        toast.warning('Disconnected from real-time updates');
      } else if (status === 'error') {
        toast.error('Real-time connection error');
      }
    }
  });

  // Provide context value
  const contextValue: WebSocketContextValue = {
    status,
    lastMessage
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext(): WebSocketContextValue {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}