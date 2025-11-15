# Frontend Documentation

Complete guide to the OmniDoc Next.js frontend architecture, components, and configuration.

## 🏗️ Architecture

The frontend is built with **Next.js 15** using the App Router:

```
┌─────────────────────────────────┐
│      Next.js 15 App Router      │
│      (React Server Components)  │
└──────────────┬──────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────┐         ┌──────────────┐
│  Pages  │         │  Components │
│         │         │             │
│ - Home  │         │ - Header    │
│ - Status│         │ - Document  │
│ - Results│        │   Selector  │
└─────────┘         └──────────────┘
    │                     │
    └──────────┬──────────┘
               │
               ▼
    ┌──────────────────┐
    │   FastAPI Backend │
    │   (Port 8000)     │
    └──────────────────┘
```

## 📁 Project Structure

```
frontend/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout with Header/Footer
│   ├── page.tsx             # Home page
│   ├── globals.css          # Global styles
│   └── project/
│       └── [id]/
│           ├── page.tsx     # Project status page
│           └── results/
│               └── page.tsx # Results viewer
├── components/              # React components
│   ├── Header.tsx           # Navigation header
│   ├── Footer.tsx           # Footer
│   ├── HeroSection.tsx      # Hero section
│   ├── HowItWorks.tsx       # How it works section
│   ├── TemplateSelector.tsx # Document template selection
│   ├── OptionsSelector.tsx  # View/organization mode selector
│   ├── DocumentSelector.tsx # Document selection (by category/level)
│   ├── PlaceholdersAndVanishInput.tsx # Input with dynamic placeholders
│   ├── ProgressTimeline.tsx # Progress display
│   ├── GeneratingAnimation.tsx
│   ├── DocumentViewer.tsx   # Document viewer
│   └── ErrorBoundary.tsx    # Error boundary component
├── lib/                      # Utilities
│   ├── api.ts               # API client
│   ├── i18n.ts              # Internationalization
│   ├── documentRanking.ts   # Document ranking
│   └── useProjectStatus.ts  # Status polling hook
└── public/                   # Static assets
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm

### Installation

```bash
cd frontend
pnpm install  # or npm install
```

### Development

```bash
pnpm dev  # Starts on http://localhost:3000
```

### Build for Production

```bash
pnpm build
pnpm start
```

### Environment Variables

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## 🎨 Components

### Header

Global navigation with language selector:

```tsx
<Header />
```

**Features:**
- Logo and branding
- GitHub link
- Language dropdown (en, zh, ja, ko, es)
- Responsive design

### TemplateSelector

Document template selection (preset combinations):

```tsx
<TemplateSelector
  selectedDocuments={selected}
  onSelectionChange={setSelected}
/>
```

**Features:**
- 9 preset templates (Developer, PM, Founder, etc.)
- One-click template application
- Visual template cards with icons
- Multi-language support

### OptionsSelector

View and organization mode selector:

```tsx
<OptionsSelector
  selectedDocuments={selected}
  onSelectionChange={setSelected}
  viewMode={viewMode}
  onViewModeChange={setViewMode}
  organizationMode={organizationMode}
  onOrganizationModeChange={setOrganizationMode}
/>
```

**Features:**
- Collapsible interface
- View modes: All, Team, Solo
- Organization modes: Category, Level
- Contains DocumentSelector when expanded

### DocumentSelector

Document selection with filtering:

```tsx
<DocumentSelector
  selectedDocuments={selected}
  onSelectionChange={setSelected}
  viewMode={viewMode}
  organizationMode={organizationMode}
/>
```

**Features:**
- View modes: All, Team, Solo
- Organization: Category or Level
- Dependency display
- Priority indicators
- Multi-language support

### PlaceholdersAndVanishInput

Input component with dynamic placeholders (Aceternity UI):

```tsx
<PlaceholdersAndVanishInput
  placeholders={placeholders}
  value={userIdea}
  onChange={handleChange}
  onSubmit={handleSubmit}
  disabled={isSubmitting}
/>
```

**Features:**
- Rotating placeholders based on language
- Vanish animation on submit
- Send button inside input box
- Character limit (5000 chars)
- Multi-language placeholders

### ProgressTimeline

Real-time progress display:

```tsx
<ProgressTimeline
  projectId={projectId}
  selectedDocuments={documents}
/>
```

**Features:**
- WebSocket real-time updates
- Fallback polling
- Phase visualization
- Document status tracking

### DocumentViewer

Two-column document viewer:

```tsx
<DocumentViewer
  documents={documents}
  projectId={projectId}
/>
```

**Features:**
- Sidebar navigation
- Markdown rendering
- Syntax highlighting
- Download functionality

## 🌐 Internationalization (i18n)

### Supported Languages

- English (en)
- 中文 (zh)
- 日本語 (ja)
- 한국어 (ko)
- Español (es)

### Usage

```tsx
import { useI18n } from '@/lib/i18n';

function MyComponent() {
  const { t, language, setLanguage } = useI18n();
  
  return (
    <div>
      <h1>{t('app.title')}</h1>
      <button onClick={() => setLanguage('zh')}>
        Switch to Chinese
      </button>
    </div>
  );
}
```

### Translation Keys

All translations are in `frontend/lib/i18n.ts`:

- `app.*` - App metadata
- `project.*` - Project-related
- `documents.*` - Document selection
- `button.*` - Buttons
- `error.*` - Error messages
- `status.*` - Status messages
- `results.*` - Results page
- `level.*` - Document levels
- `hero.*` - Hero section
- `howItWorks.*` - How it works
- `doc.name.*` - Document names

## 🔌 API Integration

### API Client

Located in `frontend/lib/api.ts`:

```typescript
import { getDocumentTemplates, createProject } from '@/lib/api';

// Get templates
const templates = await getDocumentTemplates();

// Create project
const project = await createProject({
  user_idea: "Build a task app",
  selected_documents: ["requirements", "technical_doc"]
});
```

### WebSocket Connection

Real-time updates via WebSocket:

```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/${projectId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // Handle: connected, progress, complete, error
};
```

### Polling Fallback

Automatic fallback when WebSocket unavailable:

```typescript
import { useProjectStatus } from '@/lib/useProjectStatus';

const { status, error } = useProjectStatus(projectId);
```

## 🎯 Key Features

### 1. Document Selection

- **Template Selection**: 9 preset templates for common use cases
- **View Modes**: All, Team, Solo
- **Organization**: By category or by level
- **Filtering**: By level, priority, stage
- **Dependencies**: Visual dependency display with smart recommendations
- **Persistence**: LocalStorage for selections

### 2. Real-time Updates

- **WebSocket**: Primary method
- **Polling**: Fallback mechanism
- **Status Display**: Visual progress timeline
- **Error Handling**: Graceful degradation

### 3. Document Viewing

- **Two-column Layout**: Sidebar + content
- **Markdown Rendering**: Syntax highlighting
- **Download**: Individual and bulk download
- **Share**: Share functionality

### 4. Responsive Design

- **Mobile-first**: Tailwind CSS
- **Breakpoints**: sm, md, lg, xl
- **Touch-friendly**: Mobile interactions

## 🔧 Configuration

### Next.js Config

`frontend/next.config.ts`:

```typescript
const nextConfig = {
  // API proxy (if needed)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_BASE}/api/:path*`,
      },
    ];
  },
};
```

### Tailwind CSS

`frontend/tailwind.config.js`:

```javascript
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
};
```

## 🧪 Development

### TypeScript

All components are TypeScript:

```typescript
interface DocumentSelectorProps {
  selectedDocuments: string[];
  onSelectionChange: (selected: string[]) => void;
}
```

### Linting

```bash
pnpm lint
```

### Testing

```bash
# Run tests (if configured)
pnpm test
```

## 🐛 Troubleshooting

### Hydration Errors

If you see hydration warnings:

```tsx
<div suppressHydrationWarning>
  {t('translated.text')}
</div>
```

### API Connection Issues

```bash
# Check backend is running
curl http://localhost:8000/docs

# Check CORS settings
# Update ALLOWED_ORIGINS in backend .env
```

### Build Errors

```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules
pnpm install

# Rebuild
pnpm build
```

## 🎨 UI Improvements

A comprehensive UI improvement roadmap is available:
- **[UI_IMPROVEMENTS.md](../UI_IMPROVEMENTS.md)** - 25 UI improvements organized by priority
  - Color palette implementation
  - Typography system
  - Component standardization
  - Accessibility improvements
  - Onboarding flow
  - And more...

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Documentation](https://react.dev)
- [UI Improvements Roadmap](../UI_IMPROVEMENTS.md)
- [Deployment Strategy](../DEPLOYMENT_STRATEGY.md)

