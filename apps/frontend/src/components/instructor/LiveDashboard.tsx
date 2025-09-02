/**
 * Live Dashboard Component - Shows real-time instructor analytics
 * Example usage of WebSocket integration with Zustand store
 */
'use client';

import React from 'react';
import { useAppStore } from '@/stores/app-store';
import { useWebSocketContext } from '@/components/providers/WebSocketProvider';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CheckCircle, AlertCircle, Users, TrendingUp, DollarSign, Clock } from 'lucide-react';

export function LiveDashboard() {
  const { 
    wsStatus,
    liveConfusions,
    liveAnalytics,
    activeStudents,
    unreadNotifications,
    markConfusionResolved,
    clearNotifications
  } = useAppStore();

  const { status } = useWebSocketContext();

  const handleResolveConfusion = (confusionId: string) => {
    markConfusionResolved(confusionId);
    // TODO: Also send API request to mark as resolved in backend
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Real-time Connection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              status === 'connected' ? 'bg-green-500' : 
              status === 'connecting' ? 'bg-yellow-500' : 
              'bg-red-500'
            }`} />
            <span className="text-sm text-muted-foreground capitalize">{status}</span>
            {unreadNotifications > 0 && (
              <Badge variant="secondary" onClick={clearNotifications} className="cursor-pointer">
                {unreadNotifications} new
              </Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Live Analytics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Students</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{liveAnalytics.activeStudents || 0}</div>
            <p className="text-xs text-muted-foreground">
              of {liveAnalytics.totalStudents || 0} total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {liveAnalytics.completionRate ? `${liveAnalytics.completionRate}%` : '0%'}
            </div>
            <p className="text-xs text-muted-foreground">Live updates</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Progress</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {liveAnalytics.avgProgress ? `${liveAnalytics.avgProgress}%` : '0%'}
            </div>
            <p className="text-xs text-muted-foreground">Real-time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unresolved Issues</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {liveConfusions.filter(c => !c.resolved).length}
            </div>
            <p className="text-xs text-muted-foreground">Need attention</p>
          </CardContent>
        </Card>
      </div>

      {/* Live Confusions */}
      <Card>
        <CardHeader>
          <CardTitle>Student Confusions</CardTitle>
          <p className="text-sm text-muted-foreground">
            Real-time confusion reports from your students
          </p>
        </CardHeader>
        <CardContent>
          {liveConfusions.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              No confusions reported yet
            </p>
          ) : (
            <div className="space-y-3">
              {liveConfusions.slice(0, 5).map((confusion) => (
                <div 
                  key={confusion.id} 
                  className={`p-3 rounded-lg border ${
                    confusion.resolved ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-medium">{confusion.studentName}</span>
                        <Badge variant={confusion.resolved ? 'default' : 'destructive'}>
                          {confusion.resolved ? 'Resolved' : 'Active'}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{confusion.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(confusion.timestamp).toLocaleString()}
                      </p>
                    </div>
                    {!confusion.resolved && (
                      <Button 
                        size="sm" 
                        onClick={() => handleResolveConfusion(confusion.id)}
                        className="ml-2"
                      >
                        <CheckCircle className="h-4 w-4 mr-1" />
                        Resolve
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Active Students */}
      <Card>
        <CardHeader>
          <CardTitle>Currently Active Students</CardTitle>
          <p className="text-sm text-muted-foreground">
            Students currently watching your content
          </p>
        </CardHeader>
        <CardContent>
          {activeStudents.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              No students currently active
            </p>
          ) : (
            <div className="space-y-2">
              {activeStudents.slice(0, 10).map((student) => (
                <div key={student.id} className="flex items-center justify-between p-2 rounded-lg bg-gray-50">
                  <div>
                    <span className="font-medium">{student.name}</span>
                    <p className="text-xs text-muted-foreground">
                      Last active: {new Date(student.lastActivity).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium">{student.progress}%</span>
                    <p className="text-xs text-muted-foreground">Progress</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}