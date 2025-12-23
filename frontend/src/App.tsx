/**
 * Main App component - Laboratory Command Center Layout
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import NotesPage from './pages/NotesPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ChatPage } from './pages/ChatPage';
import { YouTubePage } from './pages/YouTubePage';
import { ResearchPage } from './pages/ResearchPage';
import SettingsPage from './pages/SettingsPage';
import ResearchDashboard from './pages/Research/ResearchDashboard';
import CreateProjectWizard from './pages/Research/CreateProjectWizard';
import ProjectDetail from './pages/Research/ProjectDetail';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './contexts/ThemeContext';
import { HexagonalNav } from './components/layout/HexagonalNav';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          {/* Full-screen layout with professional sidebar */}
          <div className="min-h-screen bg-gray-950 relative overflow-hidden">
            {/* Ambient gradient mesh background */}
            <div className="gradient-mesh" />

            {/* Sidebar Navigation - Fixed Left */}
            <HexagonalNav />

            {/* Main Content - With left padding for sidebar */}
            <main className="min-h-screen ml-20 relative z-10">
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
                  path="/research"
                  element={
                    <ErrorBoundary fallbackTitle="Research Error">
                      <ResearchPage />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/research/projects"
                  element={
                    <ErrorBoundary fallbackTitle="Research Autopilot Error">
                      <ResearchDashboard />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/research/new"
                  element={
                    <ErrorBoundary fallbackTitle="Research Autopilot Error">
                      <CreateProjectWizard />
                    </ErrorBoundary>
                  }
                />
                <Route
                  path="/research/projects/:projectId"
                  element={
                    <ErrorBoundary fallbackTitle="Research Autopilot Error">
                      <ProjectDetail />
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
