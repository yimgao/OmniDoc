/**
 * Simple i18n implementation for OmniDoc with React support
 */

'use client';

import { useState, useEffect, useCallback } from 'react';

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
    'hero.title': 'Go from Idea to Full Documentation in Minutes',
    'hero.subtitle': 'AI-powered documentation generation system that creates comprehensive project documents from a single idea',
    'hero.description': 'Transform your project idea into a complete suite of documentation with our multi-agent AI system',
    'howItWorks.title': 'How It Works',
    'howItWorks.step1.title': 'Submit Your Idea',
    'howItWorks.step1.description': 'Describe your project idea in detail',
    'howItWorks.step2.title': 'Select Documents',
    'howItWorks.step2.description': 'Choose which documents to generate',
    'howItWorks.step3.title': 'Customized Agents Work',
    'howItWorks.step3.description': 'Customized agents generate your documents',
    'howItWorks.step4.title': 'View & Download',
    'howItWorks.step4.description': 'Access your complete documentation suite',
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
    'hero.title': '几分钟内从想法到完整文档',
    'hero.subtitle': 'AI驱动的文档生成系统，从单一想法创建全面的项目文档',
    'hero.description': '使用我们的多智能体AI系统，将您的项目想法转换为完整的文档套件',
    'howItWorks.title': '工作原理',
    'howItWorks.step1.title': '提交您的想法',
    'howItWorks.step1.description': '详细描述您的项目想法',
    'howItWorks.step2.title': '选择文档',
    'howItWorks.step2.description': '选择要生成的文档',
    'howItWorks.step3.title': '定制智能体工作',
    'howItWorks.step3.description': '定制智能体生成您的文档',
    'howItWorks.step4.title': '查看和下载',
    'howItWorks.step4.description': '访问您的完整文档套件',
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
    'hero.title': 'アイデアから完全なドキュメントまで数分で',
    'hero.subtitle': '単一のアイデアから包括的なプロジェクトドキュメントを作成するAI駆動のドキュメント生成システム',
    'hero.description': 'マルチエージェントAIシステムを使用して、プロジェクトのアイデアを完全なドキュメントスイートに変換',
    'howItWorks.title': '動作方法',
    'howItWorks.step1.title': 'アイデアを提出',
    'howItWorks.step1.description': 'プロジェクトのアイデアを詳しく説明',
    'howItWorks.step2.title': 'ドキュメントを選択',
    'howItWorks.step2.description': '生成するドキュメントを選択',
    'howItWorks.step3.title': 'カスタマイズエージェントが作業',
    'howItWorks.step3.description': 'カスタマイズエージェントがドキュメントを生成',
    'howItWorks.step4.title': '表示とダウンロード',
    'howItWorks.step4.description': '完全なドキュメントスイートにアクセス',
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
    'hero.title': '아이디어에서 전체 문서까지 몇 분 안에',
    'hero.subtitle': '단일 아이디어로부터 포괄적인 프로젝트 문서를 생성하는 AI 기반 문서 생성 시스템',
    'hero.description': '다중 에이전트 AI 시스템을 사용하여 프로젝트 아이디어를 완전한 문서 제품군으로 변환',
    'howItWorks.title': '작동 방식',
    'howItWorks.step1.title': '아이디어 제출',
    'howItWorks.step1.description': '프로젝트 아이디어를 자세히 설명',
    'howItWorks.step2.title': '문서 선택',
    'howItWorks.step2.description': '생성할 문서 선택',
    'howItWorks.step3.title': '맞춤형 에이전트 작업',
    'howItWorks.step3.description': '맞춤형 에이전트가 문서 생성',
    'howItWorks.step4.title': '보기 및 다운로드',
    'howItWorks.step4.description': '완전한 문서 제품군 액세스',
  },
};

// Global language state (for non-React usage)
let globalLanguage: Language = 'en';

// Language change listeners
const listeners = new Set<() => void>();

function notifyListeners() {
  listeners.forEach(listener => listener());
}

export function setLanguage(lang: Language): void {
  if (languages.includes(lang)) {
    globalLanguage = lang;
    if (typeof window !== 'undefined') {
      localStorage.setItem('omniDoc_language', lang);
    }
    notifyListeners();
  }
}

export function getLanguage(): Language {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('omniDoc_language');
    if (saved && languages.includes(saved as Language)) {
      return saved as Language;
    }
  }
  return globalLanguage;
}

export function t(key: string): string {
  const lang = getLanguage();
  return translations[lang]?.[key] || translations.en[key] || key;
}

// React hook for i18n
export function useI18n() {
  const [language, setLanguageState] = useState<Language>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('omniDoc_language');
      if (saved && languages.includes(saved as Language)) {
        return saved as Language;
      }
    }
    return 'en';
  });

  useEffect(() => {
    const handleLanguageChange = () => {
      const newLang = getLanguage();
      setLanguageState(newLang);
    };

    listeners.add(handleLanguageChange);
    return () => {
      listeners.delete(handleLanguageChange);
    };
  }, []);

  const changeLanguage = useCallback((lang: Language) => {
    setLanguage(lang);
    setLanguageState(lang);
  }, []);

  const translate = useCallback((key: string): string => {
    return translations[language]?.[key] || translations.en[key] || key;
  }, [language]);

  return {
    language,
    setLanguage: changeLanguage,
    t: translate,
  };
}

// Initialize language from localStorage
if (typeof window !== 'undefined') {
  const saved = localStorage.getItem('omniDoc_language');
  if (saved && languages.includes(saved as Language)) {
    globalLanguage = saved as Language;
  }
}
