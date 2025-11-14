'use client';

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
}

interface ProgressTimelineProps {
  events: ProgressEvent[];
  total?: number;
}

export default function ProgressTimeline({
  events,
  total,
}: ProgressTimelineProps) {
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'start':
      case 'plan':
        return '🚀';
      case 'document_started':
        return '⏳';
      case 'document_completed':
        return '✅';
      case 'complete':
        return '🎉';
      case 'error':
        return '❌';
      default:
        return '📝';
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'start':
      case 'plan':
        return 'bg-blue-500';
      case 'document_started':
        return 'bg-yellow-500';
      case 'document_completed':
        return 'bg-green-500';
      case 'complete':
        return 'bg-purple-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getEventMessage = (event: ProgressEvent) => {
    switch (event.type) {
      case 'start':
        return 'Generation started';
      case 'plan':
        return `Planning ${event.total || '?'} documents`;
      case 'document_started':
        return `Generating: ${event.name || event.document_id}`;
      case 'document_completed':
        return `Completed: ${event.name || event.document_id}`;
      case 'complete':
        return `All done! Generated ${(event as any).files_count || 0} documents`;
      case 'error':
        return `Error: ${event.message || 'Unknown error'}`;
      default:
        return event.message || event.type;
    }
  };

  if (events.length === 0) {
    return (
      <div className="flex items-center justify-center p-8 text-gray-500">
        Waiting for progress updates...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Progress</h3>
        {total && (
          <span className="text-sm text-gray-500">
            {events.filter((e) => e.type === 'document_completed').length}/
            {total} completed
          </span>
        )}
      </div>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200" />

        <div className="space-y-4">
          {events.map((event, index) => (
            <div key={index} className="relative flex items-start space-x-4">
              {/* Icon */}
              <div
                className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full ${getEventColor(
                  event.type
                )} text-white`}
              >
                <span className="text-sm">{getEventIcon(event.type)}</span>
              </div>

              {/* Content */}
              <div className="flex-1 rounded-lg bg-white p-3 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-gray-900">
                    {getEventMessage(event)}
                  </div>
                  {event.timestamp && (
                    <div className="text-xs text-gray-500">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
                {event.index && event.total && (
                  <div className="mt-2">
                    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                      <div
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{
                          width: `${
                            (parseInt(event.index) / parseInt(event.total)) *
                            100
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

