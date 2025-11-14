'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import DocumentSelector from '@/components/DocumentSelector';
import { createProject } from '@/lib/api';
import { t } from '@/lib/i18n';

export default function Home() {
  const router = useRouter();
  const [userIdea, setUserIdea] = useState('');
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load saved selections from localStorage (client-side only)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('omniDoc_selectedDocuments');
      if (saved) {
        try {
          setSelectedDocuments(JSON.parse(saved));
        } catch (e) {
          // Ignore parse errors
        }
      }
    }
  }, []);

  // Save selections to localStorage (client-side only)
  useEffect(() => {
    if (typeof window !== 'undefined' && selectedDocuments.length > 0) {
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
      setError(t('project.idea.placeholder'));
      return;
    }

    if (selectedDocuments.length === 0) {
      setError(t('documents.select'));
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
      const errorMessage = err instanceof Error ? err.message : t('error.createProject');
      console.error('Error creating project:', err);
      setError(errorMessage);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-12">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900">
            {t('app.title')}
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            {t('app.subtitle')}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Project Idea Input */}
          <div className="rounded-lg bg-white p-6 shadow-sm">
            <label
              htmlFor="userIdea"
              className="block text-sm font-medium text-gray-700"
            >
              {t('project.idea')}
            </label>
            <textarea
              id="userIdea"
              value={userIdea}
              onChange={(e) => setUserIdea(e.target.value)}
              placeholder={t('project.idea.placeholder')}
              rows={6}
              className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
            <p className="mt-2 text-sm text-gray-500">
              {t('project.idea.description')}
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
              {isSubmitting ? t('button.creating') : t('button.generate')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
