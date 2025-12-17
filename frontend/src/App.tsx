/**
 * Main App component.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { FileText, MessageSquare, Settings, StickyNote, Youtube } from 'lucide-react';
import NotesPage from './pages/NotesPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ChatPage } from './pages/ChatPage';
import { YouTubePage } from './pages/YouTubePage';
import SettingsPage from './pages/SettingsPage';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function Navigation() {
  const location = useLocation();
  const currentPath = location.pathname;

  const navItems = [
    { path: '/chat', icon: MessageSquare, label: 'Chat', color: 'from-blue-500 to-blue-600' },
    { path: '/notes', icon: StickyNote, label: 'Notes', color: 'from-indigo-500 to-indigo-600' },
    { path: '/documents', icon: FileText, label: 'Documents', color: 'from-purple-500 to-purple-600' },
    { path: '/youtube', icon: Youtube, label: 'YouTube', color: 'from-red-500 to-red-600' },
    { path: '/settings', icon: Settings, label: 'Settings', color: 'from-stone-500 to-stone-600' },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 dark:bg-stone-900/95 backdrop-blur-xl border-b border-stone-200 dark:border-stone-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-3.5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-stone-900 dark:bg-white rounded-md flex items-center justify-center">
              <span className="text-white dark:text-stone-900 font-bold text-sm">K</span>
            </div>
            <h1 className="text-xl font-semibold text-stone-900 dark:text-white tracking-tight">
              Personal Knowledge Assistant
            </h1>
          </div>
          <nav className="flex gap-1 bg-stone-100 dark:bg-stone-800 p-1 rounded-md">
            {navItems.map(({ path, icon: Icon, label }) => {
              const isActive = currentPath === path;
              return (
                <Link
                  key={path}
                  to={path}
                  className={`
                    group relative flex items-center gap-2 px-3.5 py-2 rounded-md font-medium transition-all duration-150
                    ${
                      isActive
                        ? 'bg-white dark:bg-stone-900 text-stone-900 dark:text-white shadow-sm'
                        : 'text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-white hover:bg-white/60 dark:hover:bg-stone-900/60'
                    }
                  `}
                >
                  <Icon size={16} className="flex-shrink-0" />
                  <span className="text-sm">{label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <div className="min-h-screen bg-stone-50 dark:bg-stone-950">
            <Navigation />
            <main>
              <Routes>
                <Route path="/" element={<Navigate to="/chat" replace />} />
                <Route
                  path="/chat"
                  element={
                    <ErrorBoundary fallbackTitle="Chat Error">
                      <ChatPage />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/notes"
                  element={
                    <ErrorBoundary fallbackTitle="Notes Error">
                      <NotesPage />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/documents"
                  element={
                    <ErrorBoundary fallbackTitle="Documents Error">
                      <DocumentsPage />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/youtube"
                  element={
                    <ErrorBoundary fallbackTitle="YouTube Error">
                      <YouTubePage />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <ErrorBoundary fallbackTitle="Settings Error">
                      <SettingsPage />
                    </ErrorBoundary>
                  }
                />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
