/**
 * Simple i18n implementation for OmniDoc
 */

export type Language = 'en' | 'zh' | 'ja' | 'ko';

export const languages: Language[] = ['en', 'zh', 'ja', 'ko'];

export const languageNames: Record<Language, string> = {
  en: 'English',
  zh: '中文',
  ja: '日本語',
  ko: '한국어',
};

// Translation keys
const translations: Record<Language, Record<string, string>> = {
  en: {
    'app.title': 'OmniDoc 2.0',
    'app.subtitle': 'AI-powered documentation generation system',
    'project.idea': 'Project Idea',
    'project.idea.placeholder': 'Describe your project idea in detail...',
    'project.idea.description': 'Provide a detailed description of your project. The more details you include, the better the generated documentation will be.',
    'documents.title': 'Select Documents',
    'documents.team': 'Team View',
    'documents.solo': 'Solo View',
    'documents.all': 'All Documents',
    'documents.select': 'Select Documents to Generate',
    'documents.selected': 'Selected',
    'documents.dependencies': 'Dependencies',
    'documents.priority.high': 'High Priority',
    'documents.priority.medium': 'Medium Priority',
    'documents.priority.low': 'Low Priority',
    'documents.stage.mvp': 'MVP',
    'documents.stage.iteration': 'Post-MVP',
    'documents.audience.team': 'Team',
    'documents.audience.solo': 'Solo',
    'documents.audience.mixed': 'Mixed',
    'button.generate': 'Generate Documents',
    'button.creating': 'Creating Project...',
    'button.viewResults': 'View Results',
    'error.network': 'Network Error',
    'error.loadDocuments': 'Failed to load documents',
    'error.createProject': 'Failed to create project',
    'status.title': 'Project Status',
    'status.connected': 'Real-time updates connected',
    'status.polling': 'Polling for updates (WebSocket unavailable)',
  },
  zh: {
    'app.title': 'OmniDoc 2.0',
    'app.subtitle': 'AI驱动的文档生成系统',
    'project.idea': '项目想法',
    'project.idea.placeholder': '详细描述您的项目想法...',
    'project.idea.description': '请提供您项目的详细描述。包含的细节越多，生成的文档质量越好。',
    'documents.title': '选择文档',
    'documents.team': '团队视图',
    'documents.solo': '个人视图',
    'documents.all': '所有文档',
    'documents.select': '选择要生成的文档',
    'documents.selected': '已选择',
    'documents.dependencies': '依赖关系',
    'documents.priority.high': '高优先级',
    'documents.priority.medium': '中优先级',
    'documents.priority.low': '低优先级',
    'documents.stage.mvp': 'MVP阶段',
    'documents.stage.iteration': '后续迭代',
    'documents.audience.team': '团队',
    'documents.audience.solo': '个人',
    'documents.audience.mixed': '混合',
    'button.generate': '生成文档',
    'button.creating': '正在创建项目...',
    'button.viewResults': '查看结果',
    'error.network': '网络错误',
    'error.loadDocuments': '加载文档失败',
    'error.createProject': '创建项目失败',
    'status.title': '项目状态',
    'status.connected': '实时更新已连接',
    'status.polling': '轮询更新（WebSocket不可用）',
  },
  ja: {
    'app.title': 'OmniDoc 2.0',
    'app.subtitle': 'AI駆動のドキュメント生成システム',
    'project.idea': 'プロジェクトのアイデア',
    'project.idea.placeholder': 'プロジェクトのアイデアを詳しく説明してください...',
    'project.idea.description': 'プロジェクトの詳細な説明を提供してください。詳細を多く含めるほど、生成されるドキュメントの品質が向上します。',
    'documents.title': 'ドキュメントを選択',
    'documents.team': 'チームビュー',
    'documents.solo': 'ソロビュー',
    'documents.all': 'すべてのドキュメント',
    'documents.select': '生成するドキュメントを選択',
    'documents.selected': '選択済み',
    'documents.dependencies': '依存関係',
    'documents.priority.high': '高優先度',
    'documents.priority.medium': '中優先度',
    'documents.priority.low': '低優先度',
    'documents.stage.mvp': 'MVP',
    'documents.stage.iteration': '後続イテレーション',
    'documents.audience.team': 'チーム',
    'documents.audience.solo': 'ソロ',
    'documents.audience.mixed': '混合',
    'button.generate': 'ドキュメントを生成',
    'button.creating': 'プロジェクトを作成中...',
    'button.viewResults': '結果を表示',
    'error.network': 'ネットワークエラー',
    'error.loadDocuments': 'ドキュメントの読み込みに失敗しました',
    'error.createProject': 'プロジェクトの作成に失敗しました',
    'status.title': 'プロジェクトステータス',
    'status.connected': 'リアルタイム更新が接続されました',
    'status.polling': '更新をポーリング中（WebSocket利用不可）',
  },
  ko: {
    'app.title': 'OmniDoc 2.0',
    'app.subtitle': 'AI 기반 문서 생성 시스템',
    'project.idea': '프로젝트 아이디어',
    'project.idea.placeholder': '프로젝트 아이디어를 자세히 설명하세요...',
    'project.idea.description': '프로젝트에 대한 자세한 설명을 제공하세요. 더 많은 세부 정보를 포함할수록 생성되는 문서의 품질이 향상됩니다.',
    'documents.title': '문서 선택',
    'documents.team': '팀 보기',
    'documents.solo': '솔로 보기',
    'documents.all': '모든 문서',
    'documents.select': '생성할 문서 선택',
    'documents.selected': '선택됨',
    'documents.dependencies': '의존성',
    'documents.priority.high': '높은 우선순위',
    'documents.priority.medium': '중간 우선순위',
    'documents.priority.low': '낮은 우선순위',
    'documents.stage.mvp': 'MVP',
    'documents.stage.iteration': '후속 반복',
    'documents.audience.team': '팀',
    'documents.audience.solo': '솔로',
    'documents.audience.mixed': '혼합',
    'button.generate': '문서 생성',
    'button.creating': '프로젝트 생성 중...',
    'button.viewResults': '결과 보기',
    'error.network': '네트워크 오류',
    'error.loadDocuments': '문서 로드 실패',
    'error.createProject': '프로젝트 생성 실패',
    'status.title': '프로젝트 상태',
    'status.connected': '실시간 업데이트 연결됨',
    'status.polling': '업데이트 폴링 중 (WebSocket 사용 불가)',
  },
};

let currentLanguage: Language = 'en';

export function setLanguage(lang: Language): void {
  if (languages.includes(lang)) {
    currentLanguage = lang;
    if (typeof window !== 'undefined') {
      localStorage.setItem('omniDoc_language', lang);
    }
  }
}

export function getLanguage(): Language {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('omniDoc_language');
    if (saved && languages.includes(saved as Language)) {
      return saved as Language;
    }
  }
  return currentLanguage;
}

export function t(key: string): string {
  const lang = getLanguage();
  return translations[lang]?.[key] || translations.en[key] || key;
}

// Initialize language from localStorage
if (typeof window !== 'undefined') {
  const saved = localStorage.getItem('omniDoc_language');
  if (saved && languages.includes(saved as Language)) {
    currentLanguage = saved as Language;
  }
}

