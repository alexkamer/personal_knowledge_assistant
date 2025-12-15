/**
 * Main App component.
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { FileText, MessageSquare, StickyNote } from 'lucide-react';
import NotesPage from './pages/NotesPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ChatPage } from './pages/ChatPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

type Page = 'notes' | 'documents' | 'chat';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('chat');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-4">
              <h1 className="text-2xl font-bold text-gray-900">
                Personal Knowledge Assistant
              </h1>
              <nav className="flex gap-2">
                <button
                  onClick={() => setCurrentPage('chat')}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                    ${
                      currentPage === 'chat'
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }
                  `}
                >
                  <MessageSquare size={18} />
                  Chat
                </button>
                <button
                  onClick={() => setCurrentPage('notes')}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                    ${
                      currentPage === 'notes'
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }
                  `}
                >
                  <StickyNote size={18} />
                  Notes
                </button>
                <button
                  onClick={() => setCurrentPage('documents')}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-md transition-colors
                    ${
                      currentPage === 'documents'
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }
                  `}
                >
                  <FileText size={18} />
                  Documents
                </button>
              </nav>
            </div>
          </div>
        </header>
        <main>
          {currentPage === 'chat' && <ChatPage />}
          {currentPage === 'notes' && <NotesPage />}
          {currentPage === 'documents' && <DocumentsPage />}
        </main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
