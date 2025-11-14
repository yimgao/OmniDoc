/**
 * SWR hook for polling project status as a fallback when WebSocket is unavailable.
 */
import useSWR from 'swr';
import { getProjectStatus, ProjectStatusResponse } from './api';

export function useProjectStatus(
  projectId: string | null,
  options?: {
    refreshInterval?: number;
    enabled?: boolean;
  }
) {
  const { refreshInterval = 2000, enabled = true } = options || {};

  const { data, error, isLoading, mutate } = useSWR<ProjectStatusResponse>(
    enabled && projectId ? [`project-status`, projectId] : null,
    ([, id]: [string, string]) => getProjectStatus(id),
    {
      refreshInterval: enabled ? refreshInterval : 0,
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
    }
  );

  return {
    status: data,
    isLoading,
    isError: error,
    mutate,
  };
}

