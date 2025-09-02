/**
 * WebSocket slice for managing real-time events in the Zustand store
 */
import { StateCreator } from 'zustand'

export interface WebSocketEvent {
  id: string;
  type: string;
  data: any;
  timestamp: string;
  processed?: boolean;
}

export interface WebSocketSlice {
  // State
  wsConnected: boolean;
  wsStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  recentEvents: WebSocketEvent[];
  unreadNotifications: number;
  
  // Live data from WebSocket
  liveConfusions: Array<{
    id: string;
    courseId: string;
    lessonId: string;
    studentId: string;
    studentName: string;
    message: string;
    timestamp: string;
    resolved: boolean;
  }>;
  
  liveAnalytics: {
    courseId?: string;
    totalStudents?: number;
    activeStudents?: number;
    completionRate?: number;
    avgProgress?: number;
  };
  
  activeStudents: Array<{
    id: string;
    name: string;
    lastActivity: string;
    progress: number;
  }>;
  
  // Actions
  setWsStatus: (status: WebSocketSlice['wsStatus']) => void;
  addWebSocketEvent: (event: Omit<WebSocketEvent, 'id'>) => void;
  
  // Event handlers
  handleConfusionEvent: (data: any) => void;
  handleAnalyticsUpdate: (data: any) => void;
  handleStudentProgress: (data: any) => void;
  handleEnrollmentUpdate: (data: any) => void;
  handleNotification: (data: any) => void;
  
  // Utility actions
  markConfusionResolved: (confusionId: string) => void;
  clearRecentEvents: () => void;
  clearNotifications: () => void;
}

export const createWebSocketSlice: StateCreator<WebSocketSlice> = (set, get) => ({
  // Initial state
  wsConnected: false,
  wsStatus: 'disconnected',
  recentEvents: [],
  unreadNotifications: 0,
  liveConfusions: [],
  liveAnalytics: {},
  activeStudents: [],
  
  // Actions
  setWsStatus: (status) => set({ 
    wsStatus: status, 
    wsConnected: status === 'connected' 
  }),
  
  addWebSocketEvent: (event) => set((state) => ({
    recentEvents: [
      {
        ...event,
        id: `${event.type}_${Date.now()}_${Math.random()}`,
        processed: false
      },
      ...state.recentEvents
    ].slice(0, 100) // Keep last 100 events
  })),
  
  // Event handlers
  handleConfusionEvent: (data) => set((state) => {
    const confusion = {
      id: data.confusion_id || `confusion_${Date.now()}`,
      courseId: data.course_id,
      lessonId: data.lesson_id,
      studentId: data.student_id,
      studentName: data.student_name,
      message: data.message,
      timestamp: data.timestamp,
      resolved: false
    };
    
    return {
      liveConfusions: [confusion, ...state.liveConfusions].slice(0, 50),
      unreadNotifications: state.unreadNotifications + 1
    };
  }),
  
  handleAnalyticsUpdate: (data) => set({
    liveAnalytics: {
      courseId: data.course_id,
      totalStudents: data.total_students,
      activeStudents: data.active_students,
      completionRate: data.completion_rate,
      avgProgress: data.avg_progress
    }
  }),
  
  handleStudentProgress: (data) => set((state) => {
    const studentIndex = state.activeStudents.findIndex(s => s.id === data.student_id);
    const student = {
      id: data.student_id,
      name: data.student_name || 'Unknown',
      lastActivity: new Date().toISOString(),
      progress: data.progress
    };
    
    if (studentIndex >= 0) {
      const updatedStudents = [...state.activeStudents];
      updatedStudents[studentIndex] = student;
      return { activeStudents: updatedStudents };
    } else {
      return { 
        activeStudents: [student, ...state.activeStudents].slice(0, 100)
      };
    }
  }),
  
  handleEnrollmentUpdate: (data) => set((state) => {
    // Update analytics if it's for the current course
    if (data.course_id === state.liveAnalytics.courseId) {
      return {
        liveAnalytics: {
          ...state.liveAnalytics,
          totalStudents: (state.liveAnalytics.totalStudents || 0) + 
            (data.action === 'new_enrollment' ? 1 : -1)
        },
        unreadNotifications: state.unreadNotifications + 1
      };
    }
    return { unreadNotifications: state.unreadNotifications + 1 };
  }),
  
  handleNotification: (data) => set((state) => ({
    unreadNotifications: state.unreadNotifications + 1,
    recentEvents: [
      {
        id: `notification_${Date.now()}`,
        type: 'notification',
        data: data,
        timestamp: data.timestamp || new Date().toISOString(),
        processed: false
      },
      ...state.recentEvents
    ].slice(0, 100)
  })),
  
  // Utility actions
  markConfusionResolved: (confusionId) => set((state) => ({
    liveConfusions: state.liveConfusions.map(c => 
      c.id === confusionId ? { ...c, resolved: true } : c
    )
  })),
  
  clearRecentEvents: () => set({ recentEvents: [] }),
  
  clearNotifications: () => set({ unreadNotifications: 0 })
})