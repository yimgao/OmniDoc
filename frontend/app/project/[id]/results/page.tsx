'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import useSWR from 'swr';
import DocumentViewer from '@/components/DocumentViewer';
import { getProjectDocuments, GeneratedDocument } from '@/lib/api';
import { useI18n } from '@/lib/i18n';

// SWR fetcher function
const fetcher = async (projectId: string) => {
  const response = await getProjectDocuments(projectId);
  return response.documents;
};

export default function ProjectResultsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { t } = useI18n();
  const [shareCopied, setShareCopied] = useState(false);

  // Use SWR for data fetching with caching and revalidation
  const { data: documents = [], error, isLoading: loading } = useSWR<GeneratedDocument[]>(
    projectId ? `project-${projectId}-documents` : null,
    () => fetcher(projectId),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      dedupingInterval: 5000, // Dedupe requests within 5 seconds
      errorRetryCount: 3,
      errorRetryInterval: 1000,
    }
  );

  const handleShare = async () => {
    const url = window.location.href;
    try {
      if (navigator.share) {
        // Use native share API if available
        await navigator.share({
          title: t('results.shareTitle'),
          text: t('results.shareText'),
          url: url,
        });
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(url);
        setShareCopied(true);
        setTimeout(() => setShareCopied(false), 2000);
      }
    } catch (err) {
      // User cancelled share or clipboard failed - try fallback
      try {
        await navigator.clipboard.writeText(url);
        setShareCopied(true);
        setTimeout(() => setShareCopied(false), 2000);
      } catch (clipboardErr) {
        console.error('Failed to copy to clipboard:', clipboardErr);
        // Show error message
        alert('Failed to copy link. Please copy the URL manually: ' + url);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 px-4">
        <div className="text-sm sm:text-base text-gray-500">{t('results.loading')}</div>
      </div>
    );
  }

  if (error) {
    // Convert error to string - SWR error can be an Error object
    const errorMessage = error instanceof Error ? error.message : String(error);
    
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50 px-4">
        <div className="rounded-lg bg-red-50 p-4 sm:p-6 text-red-800 max-w-md w-full">
          <div className="text-sm sm:text-base font-medium">{t('results.errorLoading')}</div>
          <div className="mt-2 text-xs sm:text-sm break-words">{errorMessage}</div>
          <button
            onClick={() => router.push(`/project/${projectId}`)}
            className="mt-4 rounded-lg bg-red-600 px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium text-white hover:bg-red-700 w-full sm:w-auto"
          >
            {t('results.backToStatus')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50 overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
              {t('results.title')}
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-gray-600 truncate">
              {t('status.projectId')}: {projectId}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleShare}
              className="flex items-center space-x-1 sm:space-x-2 rounded-lg border border-gray-300 bg-white px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              <span>{shareCopied ? '✓' : '🔗'}</span>
              <span>{shareCopied ? t('results.copied') : t('results.share')}</span>
            </button>
            <button
              onClick={() => router.push(`/project/${projectId}`)}
              className="rounded-lg border border-gray-300 px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              {t('results.backToStatus')}
            </button>
            <button
              onClick={() => router.push('/')}
              className="rounded-lg border border-gray-300 px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              {t('results.newProject')}
            </button>
          </div>
        </div>
      </div>

      {/* Document Viewer */}
      <div className="flex-1 overflow-hidden min-h-0">
        {documents.length > 0 ? (
          <DocumentViewer documents={documents} projectId={projectId} />
        ) : (
          <div className="flex h-full items-center justify-center px-4">
            <div className="text-center text-gray-500 max-w-md">
              <div className="text-base sm:text-lg font-medium">{t('results.noDocuments')}</div>
              <div className="mt-2 text-xs sm:text-sm">
                {t('results.stillGenerating')}
              </div>
              <button
                onClick={() => router.push(`/project/${projectId}`)}
                className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-xs sm:text-sm font-medium text-white hover:bg-blue-700 w-full sm:w-auto"
              >
                {t('results.viewStatus')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

