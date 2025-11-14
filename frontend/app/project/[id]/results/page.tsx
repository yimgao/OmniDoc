'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import DocumentViewer from '@/components/DocumentViewer';
import { getProjectDocuments, GeneratedDocument } from '@/lib/api';

export default function ProjectResultsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [documents, setDocuments] = useState<GeneratedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocuments() {
      if (!projectId) return;

      try {
        const response = await getProjectDocuments(projectId);
        setDocuments(response.documents);
        setLoading(false);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load documents'
        );
        setLoading(false);
      }
    }

    loadDocuments();
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-gray-500">Loading documents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="rounded-lg bg-red-50 p-6 text-red-800">
          <div className="font-medium">Error loading documents</div>
          <div className="mt-2 text-sm">{error}</div>
          <button
            onClick={() => router.push(`/project/${projectId}`)}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          >
            Back to Status
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-gray-50">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Generated Documents
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              Project ID: {projectId}
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => router.push(`/project/${projectId}`)}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              ← Back to Status
            </button>
            <button
              onClick={() => router.push('/')}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              New Project
            </button>
          </div>
        </div>
      </div>

      {/* Document Viewer */}
      <div className="flex-1 overflow-hidden">
        {documents.length > 0 ? (
          <DocumentViewer documents={documents} projectId={projectId} />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center text-gray-500">
              <div className="text-lg font-medium">No documents generated yet</div>
              <div className="mt-2 text-sm">
                Documents may still be generating. Check back in a moment.
              </div>
              <button
                onClick={() => router.push(`/project/${projectId}`)}
                className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
              >
                View Status
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

