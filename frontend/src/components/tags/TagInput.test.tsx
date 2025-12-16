/**
 * Tests for TagInput component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { TagInput } from './TagInput';
import * as useTagsHook from '@/hooks/useTags';

// Mock the useTags hook
vi.mock('@/hooks/useTags', () => ({
  useTags: vi.fn(),
}));

describe('TagInput', () => {
  const mockOnChange = vi.fn();
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
    mockUseTags.mockReturnValue({ data: mockTagsData } as any);
  });

  describe('Rendering', () => {
    it('should render label and input', () => {
      render(<TagInput value={[]} onChange={mockOnChange} />);

      expect(screen.getByLabelText('Tags')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Add tags...')).toBeInTheDocument();
    });

    it('should render helper text', () => {
      render(<TagInput value={[]} onChange={mockOnChange} />);

      expect(screen.getByText('Press Enter to add a tag. Click X to remove.')).toBeInTheDocument();
    });

    it('should display existing tags', () => {
      render(<TagInput value={['javascript', 'react']} onChange={mockOnChange} />);

      expect(screen.getByText('javascript')).toBeInTheDocument();
      expect(screen.getByText('react')).toBeInTheDocument();
    });

    it('should not show placeholder when tags exist', () => {
      render(<TagInput value={['javascript']} onChange={mockOnChange} />);

      const input = screen.getByLabelText('Tags');
      expect(input).not.toHaveAttribute('placeholder', 'Add tags...');
    });

    it('should render remove buttons for each tag', () => {
      render(<TagInput value={['javascript', 'react']} onChange={mockOnChange} />);

      expect(screen.getByLabelText('Remove tag javascript')).toBeInTheDocument();
      expect(screen.getByLabelText('Remove tag react')).toBeInTheDocument();
    });
  });

  describe('Adding Tags', () => {
    it('should add tag when Enter is pressed', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'newtag{Enter}');

      expect(mockOnChange).toHaveBeenCalledWith(['newtag']);
    });

    it('should trim and lowercase tags before adding', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, '  NewTag  {Enter}');

      expect(mockOnChange).toHaveBeenCalledWith(['newtag']);
    });

    it('should clear input after adding tag', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...') as HTMLInputElement;
      await user.type(input, 'newtag{Enter}');

      expect(input.value).toBe('');
    });

    it('should not add duplicate tags', async () => {
      const user = userEvent.setup();
      render(<TagInput value={['javascript']} onChange={mockOnChange} />);

      const input = screen.getByLabelText('Tags');
      await user.type(input, 'javascript{Enter}');

      expect(mockOnChange).not.toHaveBeenCalled();
    });

    it('should not add empty tags', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, '   {Enter}');

      expect(mockOnChange).not.toHaveBeenCalled();
    });

    it('should prevent default form submission on Enter', async () => {
      const user = userEvent.setup();
      const mockSubmit = vi.fn((e) => e.preventDefault());

      const { container } = render(
        <form onSubmit={mockSubmit}>
          <TagInput value={[]} onChange={mockOnChange} />
        </form>
      );

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'newtag{Enter}');

      // mockOnChange should be called, but form should not submit
      expect(mockOnChange).toHaveBeenCalled();
    });
  });

  describe('Removing Tags', () => {
    it('should remove tag when X button is clicked', async () => {
      const user = userEvent.setup();
      render(<TagInput value={['javascript', 'react']} onChange={mockOnChange} />);

      const removeButton = screen.getByLabelText('Remove tag javascript');
      await user.click(removeButton);

      expect(mockOnChange).toHaveBeenCalledWith(['react']);
    });

    it('should remove last tag on Backspace when input is empty', async () => {
      const user = userEvent.setup();
      render(<TagInput value={['javascript', 'react']} onChange={mockOnChange} />);

      const input = screen.getByLabelText('Tags');
      await user.click(input);
      await user.keyboard('{Backspace}');

      expect(mockOnChange).toHaveBeenCalledWith(['javascript']);
    });

    it('should not remove tag on Backspace when input has text', async () => {
      const user = userEvent.setup();
      render(<TagInput value={['javascript', 'react']} onChange={mockOnChange} />);

      const input = screen.getByLabelText('Tags');
      await user.type(input, 'test');
      await user.keyboard('{Backspace}');

      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Autocomplete Suggestions', () => {
    it('should show suggestions when typing', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'java');

      await waitFor(() => {
        expect(screen.getByText('javascript')).toBeInTheDocument();
      });
    });

    it('should filter suggestions based on input', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'react');

      await waitFor(() => {
        expect(screen.getByText('react')).toBeInTheDocument();
        expect(screen.queryByText('javascript')).not.toBeInTheDocument();
      });
    });

    it('should show note count in suggestions', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'java');

      await waitFor(() => {
        expect(screen.getByText('(10 notes)')).toBeInTheDocument();
      });
    });

    it('should limit suggestions to 5 items', async () => {
      const manyTags = Array.from({ length: 10 }, (_, i) => ({
        id: String(i),
        name: `tag${i}`,
        note_count: i,
      }));
      mockUseTags.mockReturnValue({ data: manyTags } as any);

      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'tag');

      await waitFor(() => {
        const suggestions = screen.getAllByRole('button').filter(
          (btn) => btn.textContent?.includes('notes')
        );
        expect(suggestions.length).toBeLessThanOrEqual(5);
      });
    });

    it('should add tag when suggestion is clicked', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'java');

      await waitFor(() => {
        expect(screen.getByText('javascript')).toBeInTheDocument();
      });

      const suggestion = screen.getByText('javascript');
      await user.click(suggestion);

      expect(mockOnChange).toHaveBeenCalledWith(['javascript']);
    });

    it('should hide suggestions after clicking a suggestion', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'java');

      await waitFor(() => {
        expect(screen.getByText('javascript')).toBeInTheDocument();
      });

      const suggestion = screen.getByText('javascript');
      await user.click(suggestion);

      await waitFor(() => {
        expect(screen.queryByText('(10 notes)')).not.toBeInTheDocument();
      });
    });

    it('should not show already selected tags in suggestions', async () => {
      const user = userEvent.setup();
      render(<TagInput value={['javascript']} onChange={mockOnChange} />);

      const input = screen.getByLabelText('Tags');
      await user.type(input, 'java');

      await waitFor(() => {
        // Should not show javascript since it's already selected
        const buttons = screen.queryAllByRole('button');
        const hasSuggestion = buttons.some((btn) => btn.textContent?.includes('javascript'));
        expect(hasSuggestion).toBe(false);
      });
    });

    it('should hide suggestions on blur', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'java');

      await waitFor(() => {
        expect(screen.getByText('javascript')).toBeInTheDocument();
      });

      await user.tab();

      await waitFor(() => {
        expect(screen.queryByText('(10 notes)')).not.toBeInTheDocument();
      });
    });

    it('should show suggestions on focus if input has value', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'java');

      // Blur to hide suggestions
      await user.tab();

      await waitFor(() => {
        expect(screen.queryByText('(10 notes)')).not.toBeInTheDocument();
      });

      // Focus again to show suggestions
      await user.click(input);

      await waitFor(() => {
        expect(screen.getByText('javascript')).toBeInTheDocument();
      });
    });
  });

  describe('Disabled State', () => {
    it('should disable input when disabled prop is true', () => {
      render(<TagInput value={[]} onChange={mockOnChange} disabled={true} />);

      const input = screen.getByLabelText('Tags');
      expect(input).toBeDisabled();
    });

    it('should apply disabled styles', () => {
      const { container } = render(<TagInput value={[]} onChange={mockOnChange} disabled={true} />);

      const tagContainer = container.querySelector('.bg-gray-100');
      expect(tagContainer).toBeInTheDocument();
    });

    it('should not show remove buttons when disabled', () => {
      render(<TagInput value={['javascript', 'react']} onChange={mockOnChange} disabled={true} />);

      expect(screen.queryByLabelText('Remove tag javascript')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Remove tag react')).not.toBeInTheDocument();
    });

    it('should not focus input on container click when disabled', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <TagInput value={[]} onChange={mockOnChange} disabled={true} />
      );

      const tagContainer = container.querySelector('[class*="flex flex-wrap"]');
      if (tagContainer) {
        await user.click(tagContainer as HTMLElement);
      }

      const input = screen.getByLabelText('Tags');
      expect(input).not.toHaveFocus();
    });
  });

  describe('Container Interaction', () => {
    it('should focus input when container is clicked', async () => {
      const user = userEvent.setup();
      const { container } = render(<TagInput value={[]} onChange={mockOnChange} />);

      const tagContainer = container.querySelector('[class*="flex flex-wrap"]');
      if (tagContainer) {
        await user.click(tagContainer as HTMLElement);
      }

      const input = screen.getByPlaceholderText('Add tags...');
      expect(input).toHaveFocus();
    });
  });

  describe('Case Insensitivity', () => {
    it('should filter suggestions case-insensitively', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'JAVA');

      await waitFor(() => {
        expect(screen.getByText('javascript')).toBeInTheDocument();
      });
    });

    it('should prevent duplicate tags case-insensitively', async () => {
      const user = userEvent.setup();
      render(<TagInput value={['javascript']} onChange={mockOnChange} />);

      const input = screen.getByLabelText('Tags');
      await user.type(input, 'JavaScript{Enter}');

      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty tags data', async () => {
      mockUseTags.mockReturnValue({ data: [] } as any);

      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'test');

      // Should not show any suggestions
      await waitFor(() => {
        const buttons = screen.queryAllByRole('button');
        const hasSuggestions = buttons.some((btn) => btn.textContent?.includes('notes'));
        expect(hasSuggestions).toBe(false);
      });
    });

    it('should handle undefined tags data', async () => {
      mockUseTags.mockReturnValue({ data: undefined } as any);

      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'test');

      // Should not crash
      expect(input).toBeInTheDocument();
    });

    it('should handle special characters in tags', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, 'c++{Enter}');

      expect(mockOnChange).toHaveBeenCalledWith(['c++']);
    });

    it('should handle very long tag names', async () => {
      const user = userEvent.setup();
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const longTag = 'a'.repeat(100);
      const input = screen.getByPlaceholderText('Add tags...');
      await user.type(input, `${longTag}{Enter}`);

      expect(mockOnChange).toHaveBeenCalledWith([longTag]);
    });
  });

  describe('Accessibility', () => {
    it('should have proper label association', () => {
      render(<TagInput value={[]} onChange={mockOnChange} />);

      const input = screen.getByLabelText('Tags');
      expect(input).toHaveAttribute('id', 'tags');
    });

    it('should have accessible remove buttons', () => {
      render(<TagInput value={['javascript', 'react']} onChange={mockOnChange} />);

      const removeButtons = screen.getAllByRole('button');
      removeButtons.forEach((button) => {
        if (button.getAttribute('aria-label')?.includes('Remove')) {
          expect(button).toHaveAccessibleName();
        }
      });
    });
  });
});
