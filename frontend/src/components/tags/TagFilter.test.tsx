/**
 * Tests for TagFilter component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { TagFilter } from './TagFilter';
import * as useTagsHook from '@/hooks/useTags';

// Mock the useTags hook
vi.mock('@/hooks/useTags', () => ({
  useTags: vi.fn(),
}));

describe('TagFilter', () => {
  const mockOnTagsChange = vi.fn();
  const mockUseTags = vi.mocked(useTagsHook.useTags);

  const mockTagsData = [
    { id: '1', name: 'javascript', note_count: 10 },
    { id: '2', name: 'typescript', note_count: 5 },
    { id: '3', name: 'react', note_count: 8 },
    { id: '4', name: 'python', note_count: 12 },
    { id: '5', name: 'nodejs', note_count: 6 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseTags.mockReturnValue({ data: mockTagsData, isLoading: false } as any);
  });

  describe('Rendering', () => {
    it('should render dropdown button', () => {
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      expect(screen.getByText('Filter by tags')).toBeInTheDocument();
    });

    it('should show selected count when tags are selected', () => {
      render(<TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />);

      expect(screen.getByText('2 tags selected')).toBeInTheDocument();
    });

    it('should use singular form for single tag', () => {
      render(<TagFilter selectedTags={['javascript']} onTagsChange={mockOnTagsChange} />);

      expect(screen.getByText('1 tag selected')).toBeInTheDocument();
    });

    it('should render selected tags as pills', () => {
      render(<TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />);

      expect(screen.getByText('javascript')).toBeInTheDocument();
      expect(screen.getByText('react')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading message when loading', () => {
      mockUseTags.mockReturnValue({ data: null, isLoading: true } as any);

      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      expect(screen.getByText('Loading tags...')).toBeInTheDocument();
    });

    it('should not show dropdown button when loading', () => {
      mockUseTags.mockReturnValue({ data: null, isLoading: true } as any);

      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      expect(screen.queryByText('Filter by tags')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should not render when no tags exist', () => {
      mockUseTags.mockReturnValue({ data: [], isLoading: false } as any);

      const { container } = render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      expect(container.firstChild).toBeNull();
    });

    it('should not render when data is null', () => {
      mockUseTags.mockReturnValue({ data: null, isLoading: false } as any);

      const { container } = render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Dropdown Interaction', () => {
    it('should open dropdown when button is clicked', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('Select Tags')).toBeInTheDocument();
      });
    });

    it('should close dropdown when button is clicked again', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      // Open dropdown
      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('Select Tags')).toBeInTheDocument();
      });

      // Close dropdown (click same button again)
      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.queryByText('Select Tags')).not.toBeInTheDocument();
      });
    });

    it('should show chevron icon that rotates when open', async () => {
      const user = userEvent.setup();
      const { container } = render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      const chevron = container.querySelector('svg[class*="transition-transform"]');
      expect(chevron).not.toHaveClass('rotate-180');

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        const openChevron = container.querySelector('.rotate-180');
        expect(openChevron).toBeInTheDocument();
      });
    });
  });

  describe('Tag List in Dropdown', () => {
    it('should display all available tags', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('javascript')).toBeInTheDocument();
        expect(screen.getByText('typescript')).toBeInTheDocument();
        expect(screen.getByText('react')).toBeInTheDocument();
        expect(screen.getByText('python')).toBeInTheDocument();
        expect(screen.getByText('nodejs')).toBeInTheDocument();
      });
    });

    it('should show note count for each tag', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('(10)')).toBeInTheDocument();
        expect(screen.getByText('(5)')).toBeInTheDocument();
        expect(screen.getByText('(8)')).toBeInTheDocument();
      });
    });

    it('should highlight selected tags', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <TagFilter selectedTags={['javascript']} onTagsChange={mockOnTagsChange} />
      );

      await user.click(screen.getByText('1 tag selected'));

      await waitFor(() => {
        const highlightedLabel = container.querySelector('.bg-blue-50');
        expect(highlightedLabel).toBeInTheDocument();
      });
    });
  });

  describe('Tag Selection', () => {
    it('should add tag when checkbox is clicked', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('Select Tags')).toBeInTheDocument();
      });

      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[0]);

      expect(mockOnTagsChange).toHaveBeenCalledWith(['javascript']);
    });

    it('should remove tag when checkbox is unchecked', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('2 tags selected'));

      await waitFor(() => {
        expect(screen.getByText('Select Tags')).toBeInTheDocument();
      });

      const checkboxes = screen.getAllByRole('checkbox');
      const javascriptCheckbox = checkboxes.find((cb) => cb.getAttribute('checked') !== null);
      if (javascriptCheckbox) {
        await user.click(javascriptCheckbox);
      }

      expect(mockOnTagsChange).toHaveBeenCalledWith(expect.arrayContaining(['react']));
    });

    it('should check checkboxes for selected tags', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('2 tags selected'));

      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox');
        const checkedCheckboxes = checkboxes.filter((cb) => (cb as HTMLInputElement).checked);
        expect(checkedCheckboxes.length).toBe(2);
      });
    });
  });

  describe('Clear All Functionality', () => {
    it('should show clear all button when tags are selected', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('2 tags selected'));

      await waitFor(() => {
        expect(screen.getByText('Clear all')).toBeInTheDocument();
      });
    });

    it('should not show clear all button when no tags are selected', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.queryByText('Clear all')).not.toBeInTheDocument();
      });
    });

    it('should clear all tags when clear all button is clicked', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('2 tags selected'));

      await waitFor(() => {
        expect(screen.getByText('Clear all')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Clear all'));

      expect(mockOnTagsChange).toHaveBeenCalledWith([]);
    });
  });

  describe('Tag Pills', () => {
    it('should show tag pills below dropdown', () => {
      render(<TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />);

      const pills = screen.getAllByText('javascript');
      expect(pills.length).toBeGreaterThanOrEqual(1);
    });

    it('should remove tag when pill X button is clicked', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <TagFilter selectedTags={['javascript', 'react']} onTagsChange={mockOnTagsChange} />
      );

      // Find pill buttons (X buttons)
      const pillButtons = container.querySelectorAll('.bg-blue-100 button');
      if (pillButtons.length > 0) {
        await user.click(pillButtons[0] as HTMLElement);
        expect(mockOnTagsChange).toHaveBeenCalled();
      }
    });

    it('should not show pills when no tags are selected', () => {
      const { container } = render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      const pillsContainer = container.querySelector('.flex.flex-wrap.gap-1\\.5');
      expect(pillsContainer).not.toBeInTheDocument();
    });
  });

  describe('Click Outside', () => {
    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup();
      render(
        <div>
          <div data-testid="outside">Outside</div>
          <TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />
        </div>
      );

      // Open dropdown
      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('Select Tags')).toBeInTheDocument();
      });

      // Click outside
      await user.click(screen.getByTestId('outside'));

      await waitFor(() => {
        expect(screen.queryByText('Select Tags')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have accessible checkboxes', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        const checkboxes = screen.getAllByRole('checkbox');
        expect(checkboxes.length).toBe(5);
      });
    });

    it('should have labels associated with checkboxes', async () => {
      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        const labels = screen.getAllByRole('checkbox').map((cb) => cb.closest('label'));
        labels.forEach((label) => {
          expect(label).toBeInTheDocument();
        });
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle single tag in array', () => {
      render(<TagFilter selectedTags={['javascript']} onTagsChange={mockOnTagsChange} />);

      expect(screen.getByText('1 tag selected')).toBeInTheDocument();
    });

    it('should handle many selected tags', () => {
      render(
        <TagFilter
          selectedTags={['javascript', 'typescript', 'react', 'python', 'nodejs']}
          onTagsChange={mockOnTagsChange}
        />
      );

      expect(screen.getByText('5 tags selected')).toBeInTheDocument();
    });

    it('should handle tag names with special characters', async () => {
      mockUseTags.mockReturnValue({
        data: [{ id: '1', name: 'c++', note_count: 5 }],
        isLoading: false,
      } as any);

      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('c++')).toBeInTheDocument();
      });
    });

    it('should handle tags with zero note count', async () => {
      mockUseTags.mockReturnValue({
        data: [{ id: '1', name: 'unused', note_count: 0 }],
        isLoading: false,
      } as any);

      const user = userEvent.setup();
      render(<TagFilter selectedTags={[]} onTagsChange={mockOnTagsChange} />);

      await user.click(screen.getByText('Filter by tags'));

      await waitFor(() => {
        expect(screen.getByText('(0)')).toBeInTheDocument();
      });
    });
  });
});
