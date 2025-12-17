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

  return (
    <header className="bg-white dark:bg-gray-900 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Personal Knowledge Assistant
          </h1>
          <nav className="flex gap-2">
            <Link
              to="/chat"
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                ${
                  currentPath === '/chat'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }
              `}
            >
              <MessageSquare size={18} />
              Chat
            </Link>
            <Link
              to="/notes"
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                ${
                  currentPath === '/notes'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }
              `}
            >
              <StickyNote size={18} />
              Notes
            </Link>
            <Link
              to="/documents"
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                ${
                  currentPath === '/documents'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }
              `}
            >
              <FileText size={18} />
              Documents
            </Link>
            <Link
              to="/youtube"
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                ${
                  currentPath === '/youtube'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }
              `}
            >
              <Youtube size={18} />
              YouTube
            </Link>
            <Link
              to="/settings"
              className={`
                flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                ${
                  currentPath === '/settings'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                }
              `}
            >
              <Settings size={18} />
              Settings
            </Link>
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
          <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
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
