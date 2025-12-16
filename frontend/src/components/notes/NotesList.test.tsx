/**
 * Tests for NotesList component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import NotesList from './NotesList';
import * as useNotesHook from '@/hooks/useNotes';
import type { Note } from '@/types/note';

// Mock hooks
vi.mock('@/hooks/useNotes', () => ({
  useNotes: vi.fn(),
  useDeleteNote: vi.fn(),
  useUpdateNote: vi.fn(),
}));

describe('NotesList', () => {
  const mockOnSelectNote = vi.fn();
  const mockRefetch = vi.fn();
  const mockDeleteNote = {
    mutateAsync: vi.fn(),
    isPending: false,
  };
  const mockUpdateNote = {
    mutateAsync: vi.fn(),
  };

  const mockNotesData = {
    notes: [
      {
        id: 'note-1',
        title: 'JavaScript Basics',
        content: '{"root":{"children":[{"type":"text","text":"Learn JavaScript fundamentals"}]}}',
        tags_rel: [
          { id: 'tag-1', name: 'javascript' },
          { id: 'tag-2', name: 'programming' },
        ],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-03T00:00:00Z',
      },
      {
        id: 'note-2',
        title: 'React Components',
        content: 'Build reusable UI components',
        tags_rel: [{ id: 'tag-3', name: 'react' }],
        created_at: '2025-01-02T00:00:00Z',
        updated_at: '2025-01-02T00:00:00Z',
      },
      {
        id: 'note-3',
        title: 'Empty Note',
        content: '',
        tags_rel: [],
        created_at: '2025-01-03T00:00:00Z',
        updated_at: '2025-01-03T00:00:00Z',
      },
    ],
    total: 3,
  };

  const mockUseNotes = {
    data: mockNotesData,
    isLoading: false,
    error: null,
    refetch: mockRefetch,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(useNotesHook, 'useNotes').mockReturnValue(mockUseNotes as any);
    vi.spyOn(useNotesHook, 'useDeleteNote').mockReturnValue(mockDeleteNote as any);
    vi.spyOn(useNotesHook, 'useUpdateNote').mockReturnValue(mockUpdateNote as any);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  describe('Loading State', () => {
    it('should display loading message', () => {
      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        isLoading: true,
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('Loading notes...')).toBeInTheDocument();
    });

    it('should not display notes while loading', () => {
      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        isLoading: true,
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.queryByText('JavaScript Basics')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error message', () => {
      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        error: new Error('Network error'),
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('Failed to load notes')).toBeInTheDocument();
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should display retry button on error', () => {
      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        error: new Error('Network error'),
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should call refetch when retry is clicked', async () => {
      const user = userEvent.setup();
      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        error: new Error('Network error'),
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalledTimes(1);
    });

    it('should display API error detail', () => {
      const apiError = {
        response: {
          data: {
            detail: 'Database connection failed',
          },
        },
      };

      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        error: apiError,
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('Database connection failed')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no notes', () => {
      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        data: { notes: [], total: 0 },
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText(/No notes yet/)).toBeInTheDocument();
      expect(screen.getByText(/Create your first note/)).toBeInTheDocument();
    });

    it('should not display search bar when no notes', () => {
      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        data: { notes: [], total: 0 },
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(
        screen.queryByPlaceholderText('Search notes by title, content, or tags...')
      ).not.toBeInTheDocument();
    });
  });

  describe('Notes Display', () => {
    it('should display all notes', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
      expect(screen.getByText('React Components')).toBeInTheDocument();
      expect(screen.getByText('Empty Note')).toBeInTheDocument();
    });

    it('should display note titles', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
    });

    it('should display note preview text', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText(/Learn JavaScript fundamentals/)).toBeInTheDocument();
      expect(screen.getByText(/Build reusable UI components/)).toBeInTheDocument();
    });

    it('should display "Empty note" for notes with no content', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('Empty note')).toBeInTheDocument();
    });

    it('should display note tags', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('#javascript')).toBeInTheDocument();
      expect(screen.getByText('#programming')).toBeInTheDocument();
      expect(screen.getByText('#react')).toBeInTheDocument();
    });

    it('should display updated dates using locale-independent patterns', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const dateElements = screen.getAllByText(/Jan|1|2|3|2025/i);
      expect(dateElements.length).toBeGreaterThan(0);
    });

    it('should display search bar', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(
        screen.getByPlaceholderText('Search notes by title, content, or tags...')
      ).toBeInTheDocument();
    });
  });

  describe('Note Selection', () => {
    it('should call onSelectNote when note is clicked', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      await user.click(screen.getByText('JavaScript Basics'));

      expect(mockOnSelectNote).toHaveBeenCalledWith(mockNotesData.notes[0]);
    });

    it('should highlight selected note', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} selectedNoteId="note-1" />);

      const noteElement = screen.getByText('JavaScript Basics').closest('div.p-5');
      expect(noteElement).toHaveClass('from-blue-50');
    });

    it('should not highlight unselected notes', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} selectedNoteId="note-1" />);

      const noteElement = screen.getByText('React Components').closest('div.p-5');
      expect(noteElement).not.toHaveClass('from-blue-50');
    });
  });

  describe('Search Functionality', () => {
    it('should filter notes by title', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const searchInput = screen.getByPlaceholderText('Search notes by title, content, or tags...');
      await user.type(searchInput, 'React');

      expect(screen.getByText('React Components')).toBeInTheDocument();
      expect(screen.queryByText('JavaScript Basics')).not.toBeInTheDocument();
    });

    it('should filter notes by content', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const searchInput = screen.getByPlaceholderText('Search notes by title, content, or tags...');
      await user.type(searchInput, 'fundamentals');

      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
      expect(screen.queryByText('React Components')).not.toBeInTheDocument();
    });

    it('should filter notes by tag', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const searchInput = screen.getByPlaceholderText('Search notes by title, content, or tags...');
      await user.type(searchInput, 'react');

      expect(screen.getByText('React Components')).toBeInTheDocument();
      expect(screen.queryByText('JavaScript Basics')).not.toBeInTheDocument();
    });

    it('should be case insensitive', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const searchInput = screen.getByPlaceholderText('Search notes by title, content, or tags...');
      await user.type(searchInput, 'JAVASCRIPT');

      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
    });

    it('should show "No notes match" message when search returns no results', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const searchInput = screen.getByPlaceholderText('Search notes by title, content, or tags...');
      await user.type(searchInput, 'nonexistent');

      expect(screen.getByText('No notes match your search')).toBeInTheDocument();
      expect(screen.queryByText('JavaScript Basics')).not.toBeInTheDocument();
    });

    it('should show all notes when search is cleared', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const searchInput = screen.getByPlaceholderText('Search notes by title, content, or tags...');
      await user.type(searchInput, 'React');
      await user.clear(searchInput);

      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
      expect(screen.getByText('React Components')).toBeInTheDocument();
    });
  });

  describe('More Options Menu', () => {
    it('should show menu button for each note', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      expect(menuButtons).toHaveLength(3);
    });

    it('should open menu when button is clicked', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);

      expect(screen.getByText('Edit')).toBeInTheDocument();
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });

    it('should close menu when button is clicked again', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(menuButtons[0]);

      expect(screen.queryByText('Edit')).not.toBeInTheDocument();
    });
  });

  describe('Edit Functionality', () => {
    it('should show edit input when Edit is clicked', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Edit'));

      const input = screen.getByDisplayValue('JavaScript Basics');
      expect(input).toBeInTheDocument();
      expect(input.tagName).toBe('INPUT');
    });

    it('should save edit when form is submitted', async () => {
      const user = userEvent.setup();
      mockUpdateNote.mutateAsync.mockResolvedValue({});

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Edit'));

      const input = screen.getByDisplayValue('JavaScript Basics');
      await user.clear(input);
      await user.type(input, 'Updated Title{Enter}');

      await waitFor(() => {
        expect(mockUpdateNote.mutateAsync).toHaveBeenCalledWith({
          id: 'note-1',
          data: { title: 'Updated Title' },
        });
      });
    });

    it('should not save empty title', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Edit'));

      const input = screen.getByDisplayValue('JavaScript Basics');
      await user.clear(input);
      await user.type(input, '{Enter}');

      expect(mockUpdateNote.mutateAsync).not.toHaveBeenCalled();
    });

    it('should trim whitespace from title', async () => {
      const user = userEvent.setup();
      mockUpdateNote.mutateAsync.mockResolvedValue({});

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Edit'));

      const input = screen.getByDisplayValue('JavaScript Basics');
      await user.clear(input);
      await user.type(input, '  Updated Title  {Enter}');

      await waitFor(() => {
        expect(mockUpdateNote.mutateAsync).toHaveBeenCalledWith({
          id: 'note-1',
          data: { title: 'Updated Title' },
        });
      });
    });

    it('should cancel edit on Escape key', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Edit'));

      const input = screen.getByDisplayValue('JavaScript Basics');
      await user.clear(input);
      await user.type(input, 'Updated Title{Escape}');

      await waitFor(() => {
        expect(screen.queryByDisplayValue('Updated Title')).not.toBeInTheDocument();
      });
      expect(mockUpdateNote.mutateAsync).not.toHaveBeenCalled();
    });
  });

  describe('Delete Functionality', () => {
    it('should show confirmation dialog when delete is clicked', async () => {
      const user = userEvent.setup();
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Delete'));

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this note?');
    });

    it('should delete note when confirmed', async () => {
      const user = userEvent.setup();
      mockDeleteNote.mutateAsync.mockResolvedValue({});

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Delete'));

      await waitFor(() => {
        expect(mockDeleteNote.mutateAsync).toHaveBeenCalledWith('note-1');
      });
    });

    it('should not delete note when cancelled', async () => {
      const user = userEvent.setup();
      vi.spyOn(window, 'confirm').mockReturnValue(false);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Delete'));

      expect(mockDeleteNote.mutateAsync).not.toHaveBeenCalled();
    });

    it('should disable delete button when deletion is pending', async () => {
      const user = userEvent.setup();
      vi.spyOn(useNotesHook, 'useDeleteNote').mockReturnValue({
        ...mockDeleteNote,
        isPending: true,
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      // Need to open menu first
      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);

      const deleteButton = screen.getByText('Delete');
      expect(deleteButton).toBeDisabled();
    });
  });

  describe('Tag Filtering', () => {
    it('should pass selectedTags to useNotes hook', () => {
      const selectedTags = ['javascript', 'react'];
      render(<NotesList onSelectNote={mockOnSelectNote} selectedTags={selectedTags} />);

      expect(useNotesHook.useNotes).toHaveBeenCalledWith(selectedTags);
    });

    it('should filter notes by selected tags', () => {
      const filteredData = {
        notes: [mockNotesData.notes[0]],
        total: 1,
      };

      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        data: filteredData,
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} selectedTags={['javascript']} />);

      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
      expect(screen.queryByText('React Components')).not.toBeInTheDocument();
    });
  });

  describe('Preview Text Extraction', () => {
    it('should extract text from Lexical JSON format', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText(/Learn JavaScript fundamentals/)).toBeInTheDocument();
    });

    it('should handle plain text content', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText(/Build reusable UI components/)).toBeInTheDocument();
    });

    it('should show "Empty note" for empty content', () => {
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('Empty note')).toBeInTheDocument();
    });
  });

  describe('Click Event Propagation', () => {
    it('should not select note when menu button is clicked', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);

      expect(mockOnSelectNote).not.toHaveBeenCalled();
    });

    it('should not select note when edit input is clicked', async () => {
      const user = userEvent.setup();
      render(<NotesList onSelectNote={mockOnSelectNote} />);

      const menuButtons = screen.getAllByTitle('More options');
      await user.click(menuButtons[0]);
      await user.click(screen.getByText('Edit'));

      const input = screen.getByDisplayValue('JavaScript Basics');
      await user.click(input);

      expect(mockOnSelectNote).toHaveBeenCalledTimes(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle notes with no tags_rel', () => {
      const notesWithoutTags = {
        notes: [
          {
            ...mockNotesData.notes[0],
            tags_rel: undefined as any,
          },
        ],
        total: 1,
      };

      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        data: notesWithoutTags,
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText('JavaScript Basics')).toBeInTheDocument();
    });

    it('should handle complex JSON content', () => {
      const complexNote = {
        notes: [
          {
            id: 'note-complex',
            title: 'Complex Note',
            content:
              '{"root":{"children":[{"type":"paragraph","children":[{"type":"text","text":"First paragraph"}]},{"type":"paragraph","children":[{"type":"text","text":"Second paragraph"}]}]}}',
            tags_rel: [],
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
          },
        ],
        total: 1,
      };

      vi.spyOn(useNotesHook, 'useNotes').mockReturnValue({
        ...mockUseNotes,
        data: complexNote,
      } as any);

      render(<NotesList onSelectNote={mockOnSelectNote} />);

      expect(screen.getByText(/First paragraph/)).toBeInTheDocument();
    });
  });
});
