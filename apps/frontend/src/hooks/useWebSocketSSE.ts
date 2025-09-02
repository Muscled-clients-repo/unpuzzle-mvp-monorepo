/**
 * WebSocket hook for Server-Sent Events (SSE)
 * Single connection point for all real-time events from the server
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import { useAuthStore } from '@/stores/auth-store';

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WebSocketMessage {
  type: string;
  data?: any;
  message?: string;
  level?: string;
  timestamp?: string;
}

export interface UseWebSocketSSEOptions {
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onStatusChange?: (status: WebSocketStatus) => void;
}

const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001/ws/sse/';

export function useWebSocketSSE(options: UseWebSocketSSEOptions = {}) {
  const {
    autoConnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    onMessage,
    onStatusChange,
  } = options;

  const { token } = useAuthStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout>();
  
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  const updateStatus = useCallback((newStatus: WebSocketStatus) => {
    setStatus(newStatus);
    onStatusChange?.(newStatus);
  }, [onStatusChange]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    updateStatus('connecting');

    // Create WebSocket connection with auth token in query params
    const wsUrl = token ? `${WEBSOCKET_URL}?token=${token}` : WEBSOCKET_URL;
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        updateStatus('connected');
        reconnectAttemptsRef.current = 0;

        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Ping every 30 seconds
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Don't process pong messages
          if (message.type === 'pong') {
            return;
          }

          setLastMessage(message);
          onMessage?.(message);

          // Log important events
          if (message.type === 'confusion' || message.type === 'enrollment') {
            console.log('WebSocket event:', message);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('error');
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason);
        updateStatus('disconnected');

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }

        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      updateStatus('error');
    }
  }, [token, updateStatus, onMessage, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    // Clear ping interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    // Close WebSocket connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    reconnectAttemptsRef.current = 0;
    updateStatus('disconnected');
  }, [updateStatus]);

  // Auto-connect when token changes
  useEffect(() => {
    if (autoConnect && token) {
      connect();
    } else if (!token) {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [token, autoConnect, connect, disconnect]);

  return {
    status,
    lastMessage,
    connect,
    disconnect,
  };
}

// Type-specific event hooks

export function useConfusionEvents(onConfusion: (data: any) => void) {
  return useWebSocketSSE({
    onMessage: (message) => {
      if (message.type === 'confusion') {
        onConfusion(message.data);
      }
    },
  });
}

export function useCourseAnalyticsEvents(onAnalytics: (data: any) => void) {
  return useWebSocketSSE({
    onMessage: (message) => {
      if (message.type === 'course_analytics') {
        onAnalytics(message.data);
      }
    },
  });
}

export function useEnrollmentEvents(onEnrollment: (data: any) => void) {
  return useWebSocketSSE({
    onMessage: (message) => {
      if (message.type === 'enrollment') {
        onEnrollment(message.data);
      }
    },
  });
}

export function useNotificationEvents(onNotification: (data: any) => void) {
  return useWebSocketSSE({
    onMessage: (message) => {
      if (message.type === 'notification') {
        onNotification(message);
      }
    },
  });
}

export function useStudentProgressEvents(onProgress: (data: any) => void) {
  return useWebSocketSSE({
    onMessage: (message) => {
      if (message.type === 'student_progress') {
        onProgress(message.data);
      }
    },
  });
}