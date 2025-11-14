'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import ProgressTimeline from '@/components/ProgressTimeline';
import { useProjectStatus } from '@/lib/useProjectStatus';
import { getWebSocketUrl } from '@/lib/api';

interface ProgressEvent {
  type: string;
  project_id?: string;
  document_id?: string;
  name?: string;
  index?: string;
  total?: string;
  status?: string;
  message?: string;
  timestamp?: string;
  files_count?: number;
}

export default function ProjectStatusPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fallback polling with SWR
  const { status, isLoading } = useProjectStatus(projectId, {
    refreshInterval: wsConnected ? 0 : 2000, // Only poll if WS is not connected
    enabled: !!projectId,
  });

  // WebSocket connection
  useEffect(() => {
    if (!projectId) return;

    const connectWebSocket = () => {
      try {
        const wsUrl = getWebSocketUrl(projectId);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
          }
        };

        ws.onmessage = (event) => {
          try {
            const data: ProgressEvent = JSON.parse(event.data);
            setEvents((prev) => [...prev, data]);

            // Navigate to results when complete
            if (data.type === 'complete') {
              setTimeout(() => {
                router.push(`/project/${projectId}/results`);
              }, 2000);
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setWsConnected(false);
        };

        ws.onclose = () => {
          console.log('WebSocket closed');
          setWsConnected(false);
          // Attempt to reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, 3000);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to create WebSocket:', err);
        setWsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [projectId, router]);

  // Update events from polling status
  useEffect(() => {
    if (status && !wsConnected) {
      // Create events from status for display
      const statusEvents: ProgressEvent[] = [];
      
      if (status.status === 'in_progress') {
        statusEvents.push({
          type: 'start',
          project_id: status.project_id,
          timestamp: status.updated_at,
        });
        
        status.completed_documents.forEach((docId, index) => {
          statusEvents.push({
            type: 'document_completed',
            document_id: docId,
            index: String(index + 1),
            total: String(status.selected_documents.length),
            timestamp: status.updated_at,
          });
        });
      } else if (status.status === 'complete') {
        statusEvents.push({
          type: 'complete',
          project_id: status.project_id,
          files_count: status.completed_documents.length,
          timestamp: status.updated_at,
        });
      } else if (status.status === 'failed') {
        statusEvents.push({
          type: 'error',
          project_id: status.project_id,
          message: status.error || 'Generation failed',
          timestamp: status.updated_at,
        });
      }

      setEvents(statusEvents);
    }
  }, [status, wsConnected]);

  const handleViewResults = () => {
    router.push(`/project/${projectId}/results`);
  };

  const isComplete =
    status?.status === 'complete' ||
    events.some((e) => e.type === 'complete');

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Project Status</h1>
          <p className="mt-2 text-sm text-gray-600">Project ID: {projectId}</p>
        </div>

        {/* Connection Status */}
        <div className="mb-6 rounded-lg bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div
                className={`h-3 w-3 rounded-full ${
                  wsConnected ? 'bg-green-500' : 'bg-yellow-500'
                }`}
              />
              <span className="text-sm text-gray-700">
                {wsConnected
                  ? 'Real-time updates connected'
                  : 'Polling for updates (WebSocket unavailable)'}
              </span>
            </div>
            {status && (
              <span
                className={`rounded-full px-3 py-1 text-sm font-medium ${
                  status.status === 'complete'
                    ? 'bg-green-100 text-green-800'
                    : status.status === 'failed'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-blue-100 text-blue-800'
                }`}
              >
                {status.status}
              </span>
            )}
          </div>
        </div>

        {/* Progress Timeline */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          {isLoading && events.length === 0 ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-gray-500">Loading project status...</div>
            </div>
          ) : (
            <ProgressTimeline
              events={events}
              total={status?.selected_documents.length}
            />
          )}
        </div>

        {/* Action Buttons */}
        {isComplete && (
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleViewResults}
              className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700"
            >
              View Results →
            </button>
          </div>
        )}

        {status?.error && (
          <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-800">
            <div className="font-medium">Error:</div>
            <div className="mt-1 text-sm">{status.error}</div>
          </div>
        )}
      </div>
    </div>
  );
}

