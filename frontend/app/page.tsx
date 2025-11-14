'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DocumentSelector from '@/components/DocumentSelector';
import { createProject } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [userIdea, setUserIdea] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load saved selections from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('omniDoc_selectedDocuments');
    if (saved) {
      try {
        setSelectedDocuments(JSON.parse(saved));
      } catch (e) {
        // Ignore parse errors
      }
    }
  }, []);

  // Save selections to localStorage
  useEffect(() => {
    if (selectedDocuments.length > 0) {
      localStorage.setItem(
        'omniDoc_selectedDocuments',
        JSON.stringify(selectedDocuments)
      );
    }
  }, [selectedDocuments]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!userIdea.trim()) {
      setError('Please enter your project idea');
      return;
    }

    if (selectedDocuments.length === 0) {
      setError('Please select at least one document to generate');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await createProject({
        user_idea: userIdea.trim(),
        selected_documents: selectedDocuments,
      });

      // Navigate to project status page
      router.push(`/project/${response.project_id}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to create project. Please try again.'
      );
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-12">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900">
            OmniDoc 2.0
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            AI-powered documentation generation system
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Project Idea Input */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <label
              htmlFor="userIdea"
              className="block text-sm font-medium text-gray-700"
            >
              Project Idea
            </label>
            <textarea
              id="userIdea"
              value={userIdea}
              onChange={(e) => setUserIdea(e.target.value)}
              placeholder="Describe your project idea here... For example: 'Create a task management application with user authentication, project boards, and real-time collaboration features.'"
              rows={6}
              className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="mt-2 text-sm text-gray-500">
              Provide a detailed description of your project. The more details
              you include, the better the generated documentation will be.
            </p>
          </div>

          {/* Document Selector */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <DocumentSelector
              selectedDocuments={selectedDocuments}
              onSelectionChange={setSelectedDocuments}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-red-50 p-4 text-red-800">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting || selectedDocuments.length === 0}
              className="rounded-lg bg-blue-600 px-8 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? 'Creating Project...' : 'Generate Documents'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
