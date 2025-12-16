# Text Formatting System Documentation

## Overview

The Personal Knowledge Assistant now features a comprehensive rich text formatting system inspired by RemNote and Notion. This system provides multiple ways to format text within the outliner-based note editor.

## Architecture

### Components

The formatting system consists of three main components:

1. **OutlinerEditor** (`frontend/src/components/notes/OutlinerEditor.tsx`)
   - Core editor component with block-based editing
   - Manages formatting state and logic
   - Handles keyboard shortcuts and event detection

2. **SlashCommandMenu** (`frontend/src/components/notes/SlashCommandMenu.tsx`)
   - Dropdown menu triggered by typing `/`
   - Provides quick access to formatting options
   - Shows icons and descriptions for each command

3. **FormattingToolbar** (`frontend/src/components/notes/FormattingToolbar.tsx`)
   - Floating toolbar that appears on text selection
   - Visual buttons for formatting actions
   - Includes color and highlight pickers

### Data Flow

```
User Action → OutlinerEditor (event detection) → Format Application → Block Content Update
                     ↓
              Menu/Toolbar Display
```

## Features

### 1. Slash Commands

**Trigger**: Type `/` at the start of a line or after a space

**Available Commands**:
- **Bold**: Wraps text in `**text**` (Markdown)
- **Italic**: Wraps text in `*text*` (Markdown)
- **Underline**: Wraps text in `__text__` (Markdown)
- **Heading**: Adds `# ` prefix for heading
- **Text Color**: Opens color picker (requires additional selection)
- **Highlight**: Opens highlight picker (requires additional selection)

**Implementation**:
```typescript
// Detection in OutlinerEditor.tsx
if (e.key === '/') {
  const cursorPos = textarea.selectionStart;
  if (cursorPos === 0 || block.content[cursorPos - 1] === ' ') {
    // Show slash menu at cursor position
    setSlashMenuPosition({ top: rect.top, left: rect.left });
    setSlashMenuBlockId(blockId);
  }
}
```

### 2. Keyboard Shortcuts

**Shortcuts**:
- `Cmd+B` or `Ctrl+B`: Bold selected text
- `Cmd+I` or `Ctrl+I`: Italic selected text
- `Cmd+U` or `Ctrl+U`: Underline selected text

**Implementation**:
```typescript
if ((e.metaKey || e.ctrlKey) && !e.shiftKey) {
  if (e.key === 'b') {
    e.preventDefault();
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    if (start !== end) {
      setSelectedText({ blockId, start, end });
      applyFormatting('bold');
    }
  }
  // Similar for 'i' and 'u'
}
```

### 3. Text Selection Toolbar

**Trigger**: Select text with mouse

**Features**:
- Appears above selected text
- Quick access buttons for: Bold, Italic, Underline
- Hover-activated color picker (8 colors)
- Hover-activated highlight picker (6 colors)

**Implementation**:
```typescript
const handleMouseUp = (e: MouseEvent<HTMLTextAreaElement>, blockId: string) => {
  const textarea = e.currentTarget;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  if (start !== end) {
    const selectionRect = window.getSelection()?.getRangeAt(0).getBoundingClientRect();
    if (selectionRect) {
      setToolbarPosition({
        top: selectionRect.top + window.scrollY,
        left: selectionRect.left + window.scrollX + selectionRect.width / 2,
      });
      setSelectedText({ blockId, start, end });
    }
  }
};
```

## Formatting Syntax

### Markdown Formats

The system uses standard Markdown syntax for basic formatting:

| Format     | Syntax          | Example Input     | Rendered Output |
|------------|-----------------|-------------------|-----------------|
| Bold       | `**text**`      | `**hello**`       | **hello**       |
| Italic     | `*text*`        | `*hello*`         | *hello*         |
| Underline  | `__text__`      | `__hello__`       | <u>hello</u>    |
| Heading    | `# text`        | `# Title`         | # Title         |

### HTML Color Formats

For colors and highlights, the system uses HTML span tags:

```html
<!-- Text Color -->
<span style="color: #ef4444">red text</span>

<!-- Highlight -->
<span style="background-color: #fef08a">highlighted text</span>
```

### Color Palettes

**Text Colors** (8 options):
- Red: `#ef4444`
- Orange: `#f97316`
- Yellow: `#eab308`
- Green: `#22c55e`
- Blue: `#3b82f6`
- Purple: `#a855f7`
- Pink: `#ec4899`
- Gray: `#6b7280`

**Highlights** (6 options):
- Yellow: `#fef08a`
- Green: `#bbf7d0`
- Blue: `#bfdbfe`
- Purple: `#e9d5ff`
- Pink: `#fbcfe8`
- Red: `#fecaca`

## Code Structure

### State Management

The OutlinerEditor maintains formatting-related state:

```typescript
// Slash command menu state
const [slashMenuPosition, setSlashMenuPosition] = useState<{ top: number; left: number } | null>(null);
const [slashMenuBlockId, setSlashMenuBlockId] = useState<string | null>(null);

// Formatting toolbar state
const [toolbarPosition, setToolbarPosition] = useState<{ top: number; left: number } | null>(null);
const [selectedText, setSelectedText] = useState<{ blockId: string; start: number; end: number } | null>(null);
```

### Format Application Logic

The `applyFormatting` function handles all text transformations:

```typescript
const applyFormatting = (format: string, value?: string) => {
  if (!selectedText) return;

  const blockIndex = blocks.findIndex((b) => b.id === selectedText.blockId);
  const block = blocks[blockIndex];

  const before = block.content.substring(0, selectedText.start);
  const text = block.content.substring(selectedText.start, selectedText.end);
  const after = block.content.substring(selectedText.end);

  let formattedText = text;

  switch (format) {
    case 'bold':
      formattedText = `**${text}**`;
      break;
    case 'italic':
      formattedText = `*${text}*`;
      break;
    // ... other formats
  }

  const newContent = before + formattedText + after;
  const newBlocks = [...blocks];
  newBlocks[blockIndex] = { ...block, content: newContent };
  setBlocks(newBlocks);
};
```

## Usage Examples

### Example 1: Using Slash Commands

1. Start typing in a new block
2. Press `/` at the beginning
3. Click "Bold" from the menu
4. Type between the `**` markers: `**my bold text**`

### Example 2: Keyboard Shortcuts

1. Type some text: "This is important"
2. Select the word "important"
3. Press `Cmd+B` (or `Ctrl+B`)
4. Result: "This is **important**"

### Example 3: Text Selection Toolbar

1. Type: "Highlight this word"
2. Select "this" with your mouse
3. Toolbar appears above selection
4. Click the Highlight button (Highlighter icon)
5. Hover over it and choose Yellow
6. Result: `Highlight <span style="background-color: #fef08a">this</span> word`

## Integration with Existing System

### Block Storage

Formatted text is stored as part of the block's content string:

```typescript
interface Block {
  id: string;
  content: string;  // Contains markdown and HTML formatting
  indent: number;
}
```

### Note Saving

When a note is saved, blocks are serialized to JSON:

```typescript
// In NoteForm.tsx
const contentJSON = JSON.stringify(blocks);

await createNote.mutateAsync({
  title: autoTitle.trim(),
  content: contentJSON,  // Blocks with formatting stored here
  tag_names: tags,
});
```

### Rendering

Currently, formatted text is stored but displayed as raw markdown/HTML. To render formatted text visually:

**Future Enhancement**: Add a markdown renderer or HTML parser to display formatted text in the editor.

```typescript
// Potential future implementation
import ReactMarkdown from 'react-markdown';

<ReactMarkdown>{block.content}</ReactMarkdown>
```

## User Experience

### Visual Feedback

- **Slash Menu**: Appears instantly below cursor with smooth animation
- **Toolbar**: Positioned above selected text to avoid obscuring content
- **Color Pickers**: Hover-activated dropdowns with color swatches
- **Icons**: Uses lucide-react icons for visual clarity

### Accessibility

- All buttons have descriptive titles
- Keyboard shortcuts work with both Cmd (Mac) and Ctrl (Windows/Linux)
- Menus can be closed with Escape or by clicking outside
- Focus management ensures smooth keyboard navigation

## Troubleshooting

### Slash Menu Not Appearing

**Cause**: Menu only appears if `/` is typed at start of line or after a space

**Solution**: Ensure cursor position is correct. Check:
```typescript
if (cursorPos === 0 || block.content[cursorPos - 1] === ' ')
```

### Formatting Toolbar Not Showing

**Cause**: Toolbar only appears on mouse selection, not keyboard selection

**Solution**: Use mouse to select text, or use keyboard shortcuts directly

### Colors Not Rendering

**Cause**: Raw HTML is stored but not rendered as HTML

**Solution**: Need to add HTML rendering or markdown parser to display colors visually

## Future Enhancements

### Planned Features

1. **Visual Rendering**
   - Parse markdown/HTML and render formatted text visually
   - WYSIWYG (What You See Is What You Get) editing

2. **Additional Formats**
   - Strikethrough
   - Code inline and blocks
   - Links
   - Lists (bulleted, numbered)

3. **Format Removal**
   - "Clear Formatting" button
   - Smart detection to remove existing formats

4. **Custom Colors**
   - Color picker for custom RGB/HEX values
   - Save favorite colors

5. **Format Shortcuts Panel**
   - Help menu showing all keyboard shortcuts
   - Customizable shortcuts

## Testing

### Manual Testing Checklist

- [ ] Slash menu appears when typing `/`
- [ ] All slash commands work (Bold, Italic, Underline, Heading)
- [ ] Keyboard shortcuts work (Cmd+B, Cmd+I, Cmd+U)
- [ ] Toolbar appears on text selection
- [ ] Toolbar buttons apply formatting
- [ ] Color picker shows all 8 colors
- [ ] Highlight picker shows all 6 colors
- [ ] Formatted notes save correctly
- [ ] Formatted notes load correctly
- [ ] Menus close when clicking outside

### Automated Testing

```typescript
// Example test for applyFormatting
describe('applyFormatting', () => {
  it('should wrap text in bold markers', () => {
    const block = { id: '1', content: 'hello world', indent: 0 };
    const selectedText = { blockId: '1', start: 0, end: 5 };

    applyFormatting('bold');

    expect(block.content).toBe('**hello** world');
  });
});
```

## Performance Considerations

### Optimization Strategies

1. **Menu Positioning**: Uses `setTimeout` to ensure DOM is ready
2. **Event Throttling**: Consider debouncing mouseUp events for better performance
3. **State Updates**: Batched updates to avoid unnecessary re-renders

### Memory Management

- Menu/toolbar components unmount when closed (conditional rendering)
- Event listeners cleaned up properly
- No memory leaks from selection tracking

## Related Files

| File | Purpose |
|------|---------|
| `OutlinerEditor.tsx` | Main editor with formatting logic |
| `SlashCommandMenu.tsx` | Slash command dropdown |
| `FormattingToolbar.tsx` | Selection toolbar |
| `NoteForm.tsx` | Parent component using OutlinerEditor |
| `CLAUDE.md` | Project documentation |

## Support

For issues or questions:
1. Check console for errors
2. Review this documentation
3. Test with simple cases first
4. Open GitHub issue with reproduction steps

---

**Last Updated**: December 15, 2025
**Version**: 1.0.0
**Author**: Claude & User
