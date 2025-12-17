/**
 * Tests for KeyboardShortcutsModal component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { KeyboardShortcutsModal } from './KeyboardShortcutsModal';
import type { KeyboardShortcut } from '@/hooks/useKeyboardShortcuts';

// Mock formatShortcut since it's imported
vi.mock('@/hooks/useKeyboardShortcuts', async () => {
  const actual = await vi.importActual('@/hooks/useKeyboardShortcuts');
  return {
    ...actual,
    formatShortcut: (shortcut: KeyboardShortcut) => {
      const parts: string[] = [];
      if (shortcut.ctrl || shortcut.meta) parts.push('Ctrl');
      if (shortcut.shift) parts.push('Shift');
      if (shortcut.alt) parts.push('Alt');
      parts.push(shortcut.key.toUpperCase());
      return parts.join('+');
    },
  };
});

describe('KeyboardShortcutsModal', () => {
  const mockOnClose = vi.fn();

  const mockShortcuts: KeyboardShortcut[] = [
    {
      key: 's',
      ctrl: true,
      handler: vi.fn(),
      description: 'Save changes',
      category: 'Editing',
    },
    {
      key: 'n',
      ctrl: true,
      handler: vi.fn(),
      description: 'Create new note',
      category: 'Navigation',
    },
    {
      key: 'k',
      ctrl: true,
      handler: vi.fn(),
      description: 'Search',
      category: 'Navigation',
    },
    {
      key: '?',
      handler: vi.fn(),
      description: 'Show keyboard shortcuts',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Visibility', () => {
    it('should not render when isOpen is false', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={false} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(container.firstChild).toBeNull();
    });

    it('should render when isOpen is true', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
    });

    it('should render modal overlay', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const overlay = container.querySelector('.fixed.inset-0');
      expect(overlay).toBeInTheDocument();
    });
  });

  describe('Header', () => {
    it('should display title', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
    });

    it('should display close button', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const closeButton = screen.getByLabelText('Close');
      expect(closeButton).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const closeButton = screen.getByLabelText('Close');
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Shortcuts Display', () => {
    it('should display all shortcuts', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(screen.getByText('Save changes')).toBeInTheDocument();
      expect(screen.getByText('Create new note')).toBeInTheDocument();
      expect(screen.getByText('Search')).toBeInTheDocument();
      expect(screen.getByText('Show keyboard shortcuts')).toBeInTheDocument();
    });

    it('should display formatted shortcuts', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(screen.getByText('Ctrl+S')).toBeInTheDocument();
      expect(screen.getByText('Ctrl+N')).toBeInTheDocument();
      expect(screen.getByText('Ctrl+K')).toBeInTheDocument();
      // ? appears in both shortcuts and footer
      const questionMarks = screen.getAllByText('?');
      expect(questionMarks.length).toBeGreaterThanOrEqual(1);
    });

    it('should render shortcuts in kbd elements', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const kbdElements = container.querySelectorAll('kbd');
      // At least 4 shortcuts + 2 in footer (? and Esc)
      expect(kbdElements.length).toBeGreaterThanOrEqual(6);
    });
  });

  describe('Category Grouping', () => {
    it('should group shortcuts by category', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(screen.getByText('Editing')).toBeInTheDocument();
      expect(screen.getByText('Navigation')).toBeInTheDocument();
    });

    it('should use "General" category for shortcuts without category', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(screen.getByText('General')).toBeInTheDocument();
    });

    it('should apply uppercase styling to categories', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const categories = container.querySelectorAll('.uppercase');
      expect(categories.length).toBeGreaterThan(0);
    });

    it('should group multiple shortcuts under same category', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      // Navigation category should have 2 shortcuts
      expect(screen.getByText('Create new note')).toBeInTheDocument();
      expect(screen.getByText('Search')).toBeInTheDocument();
    });
  });

  describe('Footer', () => {
    it('should display help text', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      expect(screen.getByText(/Press/)).toBeInTheDocument();
      expect(screen.getByText(/to show this help/)).toBeInTheDocument();
      expect(screen.getByText(/to close/)).toBeInTheDocument();
    });

    it('should display ? and Esc keys in footer', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const escKey = screen.getByText('Esc');
      expect(escKey).toBeInTheDocument();

      const questionMarks = screen.getAllByText('?');
      expect(questionMarks.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Modifier Keys', () => {
    it('should display Ctrl modifier', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrl: true, handler: vi.fn(), description: 'Save' },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(screen.getByText('Ctrl+S')).toBeInTheDocument();
    });

    it('should display Shift modifier', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', shift: true, handler: vi.fn(), description: 'Save As' },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(screen.getByText('Shift+S')).toBeInTheDocument();
    });

    it('should display Alt modifier', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', alt: true, handler: vi.fn(), description: 'Alternative Save' },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(screen.getByText('Alt+S')).toBeInTheDocument();
    });

    it('should display multiple modifiers', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrl: true, shift: true, handler: vi.fn(), description: 'Special Save' },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(screen.getByText('Ctrl+Shift+S')).toBeInTheDocument();
    });

    it('should display all modifiers together', () => {
      const shortcuts: KeyboardShortcut[] = [
        {
          key: 's',
          ctrl: true,
          shift: true,
          alt: true,
          handler: vi.fn(),
          description: 'Complex Save',
        },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(screen.getByText('Ctrl+Shift+Alt+S')).toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('should handle empty shortcuts array', () => {
      render(<KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={[]} />);

      expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
      // Should still render modal structure
    });

    it('should handle shortcuts with empty descriptions', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: 's', ctrl: true, handler: vi.fn(), description: '' },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(screen.getByText('Ctrl+S')).toBeInTheDocument();
    });
  });

  describe('Styling and Layout', () => {
    it('should apply modal styling', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const modal = container.querySelector('.bg-white');
      expect(modal).toBeInTheDocument();
      expect(modal).toHaveClass('rounded-lg', 'shadow-xl');
    });

    it('should have scrollable content area', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const scrollableArea = container.querySelector('.overflow-y-auto');
      expect(scrollableArea).toBeInTheDocument();
    });

    it('should apply max height to modal', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const modal = container.querySelector('.max-h-\\[80vh\\]');
      expect(modal).toBeInTheDocument();
    });

    it('should apply hover effects to shortcut items', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const shortcutItems = container.querySelectorAll('.hover\\:bg-stone-50');
      expect(shortcutItems.length).toBeGreaterThan(0);
    });
  });

  describe('Dark Mode Support', () => {
    it('should have dark mode classes', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const darkElements = container.querySelectorAll('[class*="dark:"]');
      expect(darkElements.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('should have accessible close button', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const closeButton = screen.getByLabelText('Close');
      expect(closeButton).toHaveAttribute('aria-label', 'Close');
    });

    it('should use semantic HTML for headings', () => {
      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const mainHeading = screen.getByRole('heading', { level: 2 });
      expect(mainHeading).toHaveTextContent('Keyboard Shortcuts');
    });

    it('should use kbd elements for keyboard keys', () => {
      const { container } = render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={mockShortcuts} />
      );

      const kbdElements = container.querySelectorAll('kbd');
      expect(kbdElements.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle very long descriptions', () => {
      const shortcuts: KeyboardShortcut[] = [
        {
          key: 's',
          ctrl: true,
          handler: vi.fn(),
          description: 'This is a very long description that should wrap properly in the modal layout',
        },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(
        screen.getByText(/This is a very long description/)
      ).toBeInTheDocument();
    });

    it('should handle many shortcuts', () => {
      const manyShortcuts: KeyboardShortcut[] = Array.from({ length: 20 }, (_, i) => ({
        key: String.fromCharCode(65 + i),
        ctrl: true,
        handler: vi.fn(),
        description: `Action ${i + 1}`,
        category: `Category ${(i % 3) + 1}`,
      }));

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={manyShortcuts} />
      );

      expect(screen.getByText('Action 1')).toBeInTheDocument();
      expect(screen.getByText('Action 20')).toBeInTheDocument();
    });

    it('should handle special characters in shortcuts', () => {
      const shortcuts: KeyboardShortcut[] = [
        { key: '/', handler: vi.fn(), description: 'Search' },
        { key: '?', handler: vi.fn(), description: 'Help' },
        { key: 'Escape', handler: vi.fn(), description: 'Close' },
      ];

      render(
        <KeyboardShortcutsModal isOpen={true} onClose={mockOnClose} shortcuts={shortcuts} />
      );

      expect(screen.getByText('/')).toBeInTheDocument();
      // ? appears multiple times
      const questionMarks = screen.getAllByText('?');
      expect(questionMarks.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('ESCAPE')).toBeInTheDocument();
    });
  });
});
