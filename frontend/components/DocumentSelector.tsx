'use client';

import { useEffect, useState, useMemo } from 'react';
import { DocumentTemplate, getDocumentTemplates } from '../lib/api';
import { useI18n, getDocumentName, getLevelName } from '../lib/i18n';
import { rankDocuments, filterDocumentsByView, organizeByLevel, organizeByCategory, getRecommendedDocuments, DocumentLevel, LEVEL_ICONS, type ViewMode } from '../lib/documentRanking';
import { DocumentListSkeleton } from './ui/Skeleton';
import EmptyState from './EmptyState';

interface DocumentSelectorProps {
  selectedDocuments: string[];
  onSelectionChange: (selected: string[]) => void;
  viewMode: ViewMode;
  organizationMode: 'category' | 'level';
}

export default function DocumentSelector({
  selectedDocuments,
  onSelectionChange,
  viewMode,
  organizationMode,
}: DocumentSelectorProps) {
  const [templates, setTemplates] = useState<DocumentTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedLevels, setExpandedLevels] = useState<Set<DocumentLevel>>(new Set());
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const { t } = useI18n();

  useEffect(() => {
    async function loadTemplates() {
      try {
        const response = await getDocumentTemplates();
        setTemplates(response.documents);
        setLoading(false);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : t('error.loadDocuments');
        console.error('Error loading document templates:', err);
        setError(errorMessage);
        setLoading(false);
      }
    }
    loadTemplates();
  }, [t]);

  // Filter and rank documents
  const filteredDocs = filterDocumentsByView(templates, viewMode);
  const rankedDocs = rankDocuments(filteredDocs);
  const organizedByLevel = organizeByLevel(rankedDocs);
  const organizedByCategory = organizeByCategory(rankedDocs);

  // Calculate recommended documents based on selected documents' dependencies
  const recommendedDocs = useMemo(() => {
    const recommended = new Set<string>();
    selectedDocuments.forEach((docId) => {
      const deps = getRecommendedDocuments(docId, templates);
      deps.forEach((dep) => {
        if (!selectedDocuments.includes(dep.id)) {
          recommended.add(dep.id);
        }
      });
    });
    return Array.from(recommended).map((id) => templates.find((t) => t.id === id)).filter((doc): doc is DocumentTemplate => doc !== undefined);
  }, [selectedDocuments, templates]);


  const toggleDocument = (docId: string, autoSelectDeps: boolean = false) => {
    if (selectedDocuments.includes(docId)) {
      onSelectionChange(selectedDocuments.filter((id) => id !== docId));
    } else {
      const newSelected = [...selectedDocuments, docId];
      // Auto-select dependencies if enabled
      if (autoSelectDeps) {
        const deps = getRecommendedDocuments(docId, templates);
        deps.forEach((dep) => {
          if (!newSelected.includes(dep.id)) {
            newSelected.push(dep.id);
          }
        });
      }
      onSelectionChange(newSelected);
    }
  };

  const toggleLevel = (level: DocumentLevel) => {
    const newExpanded = new Set(expandedLevels);
    if (newExpanded.has(level)) {
      newExpanded.delete(level);
    } else {
      newExpanded.add(level);
    }
    setExpandedLevels(newExpanded);
  };

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const renderDocumentItem = (doc: DocumentTemplate, isRecommended: boolean = false) => {
    const isSelected = selectedDocuments.includes(doc.id);
    const isRecommendedSelected = isRecommended && isSelected;
    
    return (
      <label
        key={doc.id}
        className={`flex items-start space-x-3 rounded-lg border-2 p-3 transition-colors ${
          isRecommended && !isSelected
            ? 'border-blue-400 bg-blue-50 hover:bg-blue-100 shadow-sm'
            : isRecommendedSelected
            ? 'border-blue-500 bg-blue-100 hover:bg-blue-150 shadow-sm'
            : 'border-gray-200 bg-white hover:bg-gray-50'
        }`}
      >
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => toggleDocument(doc.id)}
          className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900" suppressHydrationWarning>{getDocumentName(doc.id) || doc.name}</span>
            {isRecommended && !isSelected && (
              <span className="rounded px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800" suppressHydrationWarning>
                {t('documents.recommend')}
              </span>
            )}
            {doc.priority && (
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                doc.priority.includes('高') || doc.priority.includes('High')
                  ? 'bg-red-100 text-red-800'
                  : doc.priority.includes('中') || doc.priority.includes('Medium')
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {doc.priority}
              </span>
            )}
          </div>
          {doc.dependencies && doc.dependencies.length > 0 && (
            <div className="mt-2 flex items-start gap-1 rounded-md bg-gray-50 px-2 py-1.5 text-xs" suppressHydrationWarning>
              <span className="font-medium text-gray-700">{t('documents.dependencies')}:</span>
              <span className="flex-1 text-gray-600">
                {doc.dependencies
                  .map((depId) => {
                    const depDoc = templates.find((t) => t.id === depId);
                    const depName = getDocumentName(depId) || depDoc?.name || depId;
                    const isSelected = selectedDocuments.includes(depId);
                    return (
                      <span
                        key={depId}
                        className={`inline-block rounded px-1.5 py-0.5 mr-1 ${
                          isSelected
                            ? 'bg-green-100 text-green-800 font-medium'
                            : 'bg-gray-200 text-gray-700'
                        }`}
                      >
                        {depName}
                      </span>
                    );
                  })}
              </span>
            </div>
          )}
        </div>
      </label>
    );
  };

  const renderDocumentList = (docs: DocumentTemplate[], level?: DocumentLevel, category?: string) => {
    if (docs.length === 0) return null;

    return (
      <div key={level || category} className="space-y-2">
        {docs.map((doc) => renderDocumentItem(doc))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-4">
        <DocumentListSkeleton count={5} />
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon="⚠️"
        title={t('error.loadDocuments')}
        description={error}
        primaryAction={{
          label: t('common.retry') || 'Retry',
          onClick: () => window.location.reload(),
        }}
      />
    );
  }

  return (
    <div className="space-y-4 min-h-0">

      {/* Recommended Documents */}
      {recommendedDocs.length > 0 && (
        <div className="rounded-lg border-2 border-blue-400 bg-blue-50 shadow-md">
          <div className="border-b-2 border-blue-300 bg-blue-100 p-4">
            <h4 className="flex items-center gap-2 font-semibold text-blue-900">
              <span className="text-xl">💡</span>
              <span suppressHydrationWarning>{t('documents.recommend')}</span>
              <span className="ml-auto text-sm font-normal text-blue-700">
                ({recommendedDocs.length} {t('documents.recommend')})
              </span>
            </h4>
            <p className="mt-1 text-xs text-blue-700" suppressHydrationWarning>
              {t('documents.recommend.tooltip')}
            </p>
          </div>
          <div className="p-4 space-y-2">
            {recommendedDocs.map((doc) => renderDocumentItem(doc, true))}
          </div>
        </div>
      )}

      {/* Document Count Summary */}
      <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3">
        <h3 className="text-lg font-semibold" suppressHydrationWarning>{t('documents.select')}</h3>
        <span className="text-sm text-gray-500" suppressHydrationWarning>
          {selectedDocuments.length} {t('documents.selected')} ({rankedDocs.length} {t('documents.all')})
        </span>
      </div>

      {/* Documents organized by Category or Level */}
      <div className="space-y-6">
        {organizationMode === 'category' ? (
          /* Category View */
          Object.entries(organizedByCategory)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([category, docs]) => (
              <div key={category} className="rounded-lg border-2 border-indigo-200 bg-indigo-50">
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full border-b border-indigo-200 bg-indigo-100 p-4 text-left transition-colors hover:bg-indigo-200"
                >
                  <h4 className="flex items-center gap-2 font-semibold text-indigo-900">
                    <span className="text-xl">📁</span>
                    <span suppressHydrationWarning>{category}</span>
                    <span className="ml-auto text-sm font-normal text-indigo-700">
                      ({docs.length} documents)
                    </span>
                    <span className="text-indigo-600">
                      {expandedCategories.has(category) ? '▼' : '▶'}
                    </span>
                  </h4>
                </button>
                {expandedCategories.has(category) && (
                  <div className="p-4">
                    {renderDocumentList(docs, undefined, category)}
                  </div>
                )}
              </div>
            ))
        ) : (
          /* Level View */
          <>
        {/* Level 1: Strategic */}
        {organizedByLevel.strategic.length > 0 && (
          <div className="rounded-lg border-2 border-purple-200 bg-purple-50">
            <button
              onClick={() => toggleLevel(DocumentLevel.STRATEGIC)}
              className="w-full border-b border-purple-200 bg-purple-100 p-4 text-left transition-colors hover:bg-purple-200"
            >
              <h4 className="flex items-center gap-2 font-semibold text-purple-900">
                <span className="text-xl">{LEVEL_ICONS[DocumentLevel.STRATEGIC]}</span>
                <span suppressHydrationWarning>{getLevelName(DocumentLevel.STRATEGIC)}</span>
                <span className="ml-auto text-sm font-normal text-purple-700">
                  ({organizedByLevel.strategic.length} documents)
                </span>
                <span className="text-purple-600">
                  {expandedLevels.has(DocumentLevel.STRATEGIC) ? '▼' : '▶'}
                </span>
              </h4>
            </button>
            {expandedLevels.has(DocumentLevel.STRATEGIC) && (
              <div className="p-4">
                {renderDocumentList(organizedByLevel.strategic, DocumentLevel.STRATEGIC)}
              </div>
            )}
          </div>
        )}

        {/* Level 2: Product Manager */}
        {organizedByLevel.product.length > 0 && (
          <div className="rounded-lg border-2 border-blue-200 bg-blue-50">
            <button
              onClick={() => toggleLevel(DocumentLevel.PRODUCT)}
              className="w-full border-b border-blue-200 bg-blue-100 p-4 text-left transition-colors hover:bg-blue-200"
            >
              <h4 className="flex items-center gap-2 font-semibold text-blue-900">
                <span className="text-xl">{LEVEL_ICONS[DocumentLevel.PRODUCT]}</span>
                <span suppressHydrationWarning>{getLevelName(DocumentLevel.PRODUCT)}</span>
                <span className="ml-auto text-sm font-normal text-blue-700">
                  ({organizedByLevel.product.length} documents)
                </span>
                <span className="text-blue-600">
                  {expandedLevels.has(DocumentLevel.PRODUCT) ? '▼' : '▶'}
                </span>
              </h4>
            </button>
            {expandedLevels.has(DocumentLevel.PRODUCT) && (
              <div className="p-4">
                {renderDocumentList(organizedByLevel.product, DocumentLevel.PRODUCT)}
              </div>
            )}
          </div>
        )}

        {/* Level 3: Developer/Technical */}
        {organizedByLevel.developer.length > 0 && (
          <div className="rounded-lg border-2 border-green-200 bg-green-50">
            <button
              onClick={() => toggleLevel(DocumentLevel.DEVELOPER)}
              className="w-full border-b border-green-200 bg-green-100 p-4 text-left transition-colors hover:bg-green-200"
            >
              <h4 className="flex items-center gap-2 font-semibold text-green-900">
                <span className="text-xl">{LEVEL_ICONS[DocumentLevel.DEVELOPER]}</span>
                <span suppressHydrationWarning>{getLevelName(DocumentLevel.DEVELOPER)}</span>
                <span className="ml-auto text-sm font-normal text-green-700">
                  ({organizedByLevel.developer.length} documents)
                </span>
                <span className="text-green-600">
                  {expandedLevels.has(DocumentLevel.DEVELOPER) ? '▼' : '▶'}
                </span>
              </h4>
            </button>
            {expandedLevels.has(DocumentLevel.DEVELOPER) && (
              <div className="p-4">
                {renderDocumentList(organizedByLevel.developer, DocumentLevel.DEVELOPER)}
              </div>
            )}
          </div>
        )}

        {/* Level 4: User/End-user */}
        {organizedByLevel.user.length > 0 && (
          <div className="rounded-lg border-2 border-yellow-200 bg-yellow-50">
            <button
              onClick={() => toggleLevel(DocumentLevel.USER)}
              className="w-full border-b border-yellow-200 bg-yellow-100 p-4 text-left transition-colors hover:bg-yellow-200"
            >
              <h4 className="flex items-center gap-2 font-semibold text-yellow-900">
                <span className="text-xl">{LEVEL_ICONS[DocumentLevel.USER]}</span>
                <span suppressHydrationWarning>{getLevelName(DocumentLevel.USER)}</span>
                <span className="ml-auto text-sm font-normal text-yellow-700">
                  ({organizedByLevel.user.length} documents)
                </span>
                <span className="text-yellow-600">
                  {expandedLevels.has(DocumentLevel.USER) ? '▼' : '▶'}
                </span>
              </h4>
            </button>
            {expandedLevels.has(DocumentLevel.USER) && (
              <div className="p-4">
                {renderDocumentList(organizedByLevel.user, DocumentLevel.USER)}
              </div>
            )}
          </div>
        )}

        {/* Level 5: Operations/Maintenance */}
        {organizedByLevel.operations.length > 0 && (
          <div className="rounded-lg border-2 border-orange-200 bg-orange-50">
            <button
              onClick={() => toggleLevel(DocumentLevel.OPERATIONS)}
              className="w-full border-b border-orange-200 bg-orange-100 p-4 text-left transition-colors hover:bg-orange-200"
            >
              <h4 className="flex items-center gap-2 font-semibold text-orange-900">
                <span className="text-xl">{LEVEL_ICONS[DocumentLevel.OPERATIONS]}</span>
                <span suppressHydrationWarning>{getLevelName(DocumentLevel.OPERATIONS)}</span>
                <span className="ml-auto text-sm font-normal text-orange-700">
                  ({organizedByLevel.operations.length} documents)
                </span>
                <span className="text-orange-600">
                  {expandedLevels.has(DocumentLevel.OPERATIONS) ? '▼' : '▶'}
                </span>
              </h4>
            </button>
            {expandedLevels.has(DocumentLevel.OPERATIONS) && (
              <div className="p-4">
                {renderDocumentList(organizedByLevel.operations, DocumentLevel.OPERATIONS)}
              </div>
            )}
          </div>
        )}

        {/* Cross-Level (Everyone) */}
        {organizedByLevel.crossLevel.length > 0 && (
          <div className="rounded-lg border-2 border-gray-200 bg-gray-50">
            <button
              onClick={() => toggleLevel(DocumentLevel.CROSS_LEVEL)}
              className="w-full border-b border-gray-200 bg-gray-100 p-4 text-left transition-colors hover:bg-gray-200"
            >
              <h4 className="flex items-center gap-2 font-semibold text-gray-900">
                <span className="text-xl">{LEVEL_ICONS[DocumentLevel.CROSS_LEVEL]}</span>
                <span suppressHydrationWarning>{getLevelName(DocumentLevel.CROSS_LEVEL)}</span>
                <span className="ml-auto text-sm font-normal text-gray-700">
                  ({organizedByLevel.crossLevel.length} documents)
                </span>
                <span className="text-gray-600">
                  {expandedLevels.has(DocumentLevel.CROSS_LEVEL) ? '▼' : '▶'}
                </span>
              </h4>
            </button>
            {expandedLevels.has(DocumentLevel.CROSS_LEVEL) && (
              <div className="p-4">
                {renderDocumentList(organizedByLevel.crossLevel, DocumentLevel.CROSS_LEVEL)}
              </div>
            )}
          </div>
        )}
        </>
        )}
      </div>
    </div>
  );
}
