# Formatting System Architecture

## Component Hierarchy

```
NoteForm
    └── OutlinerEditor
            ├── Block 1 (textarea)
            ├── Block 2 (textarea)
            ├── Block 3 (textarea)
            ├── SlashCommandMenu (conditional)
            └── FormattingToolbar (conditional)
```

## User Interaction Flows

### Flow 1: Slash Command

```
User types "/"
    ↓
OutlinerEditor detects "/" in keyDown handler
    ↓
Gets cursor position from textarea
    ↓
Sets slashMenuPosition and slashMenuBlockId state
    ↓
SlashCommandMenu renders at position
    ↓
User clicks command (e.g., "Bold")
    ↓
handleSlashCommand() called
    ↓
Inserts formatting markers at cursor
    ↓
Updates block content
    ↓
Menu closes
```

### Flow 2: Keyboard Shortcut

```
User selects text and presses Cmd+B
    ↓
OutlinerEditor keyDown handler detects metaKey + 'b'
    ↓
Gets selection start/end from textarea
    ↓
Calls applyFormatting('bold')
    ↓
Extracts text between start and end
    ↓
Wraps text: "text" → "**text**"
    ↓
Updates block content with formatted text
```

### Flow 3: Text Selection Toolbar

```
User selects text with mouse
    ↓
OutlinerEditor mouseUp handler fires
    ↓
Gets selection range from textarea
    ↓
Gets visual position from window.getSelection()
    ↓
Sets toolbarPosition and selectedText state
    ↓
FormattingToolbar renders at position
    ↓
User clicks format button
    ↓
onFormat() calls applyFormatting()
    ↓
Updates block content
    ↓
Toolbar closes
```

## State Management

### OutlinerEditor State

```typescript
// Core block data
const [blocks, setBlocks] = useState<Block[]>([...]);
const [focusedBlockId, setFocusedBlockId] = useState<string | null>(null);

// Menu states
const [slashMenuPosition, setSlashMenuPosition] = useState<{top, left} | null>(null);
const [slashMenuBlockId, setSlashMenuBlockId] = useState<string | null>(null);

// Toolbar states
const [toolbarPosition, setToolbarPosition] = useState<{top, left} | null>(null);
const [selectedText, setSelectedText] = useState<{blockId, start, end} | null>(null);

// Refs for DOM access
const inputRefs = useRef<{ [key: string]: HTMLTextAreaElement }>({});
```

## Event Handling

### Keyboard Events

```typescript
handleKeyDown(e: KeyboardEvent, blockId: string, blockIndex: number) {
  // Priority 1: Format shortcuts (Cmd+B, Cmd+I, Cmd+U)
  if ((e.metaKey || e.ctrlKey) && ['b', 'i', 'u'].includes(e.key)) {
    // Apply formatting
  }

  // Priority 2: Slash command detection
  if (e.key === '/') {
    // Show slash menu
  }

  // Priority 3: Navigation (Enter, Tab, Backspace, Arrows)
  if (e.key === 'Enter') {
    // Create new block
  }
}
```

### Mouse Events

```typescript
handleMouseUp(e: MouseEvent, blockId: string) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  if (start !== end) {
    // Show formatting toolbar
  } else {
    // Hide toolbar
  }
}
```

## Data Transformation

### Format Application Pipeline

```
Original Content: "This is some text"
                      ↓
User selects: start=8, end=12 → "some"
                      ↓
applyFormatting('bold') called
                      ↓
Split: before="This is ", text="some", after=" text"
                      ↓
Format: formattedText="**some**"
                      ↓
Combine: "This is **some** text"
                      ↓
Update block content
```

### Format Types

| Format | Input | Output |
|--------|-------|--------|
| Bold | "text" | "**text**" |
| Italic | "text" | "*text*" |
| Underline | "text" | "__text__" |
| Color | "text" | `<span style="color: #ef4444">text</span>` |
| Highlight | "text" | `<span style="background-color: #fef08a">text</span>` |
| Heading | "" | "# " |

## Menu Positioning

### Slash Menu Position

```
Cursor Position
    ↓
Get textarea.getBoundingClientRect()
    ↓
Calculate: {
  top: rect.top + window.scrollY,
  left: rect.left + window.scrollX
}
    ↓
Position menu at cursor
```

### Toolbar Position

```
Text Selection
    ↓
Get window.getSelection().getRangeAt(0).getBoundingClientRect()
    ↓
Calculate: {
  top: selectionRect.top + window.scrollY - 50,  // 50px above
  left: selectionRect.left + window.scrollX + (width / 2)  // centered
}
    ↓
Position toolbar above selection
```

## Component Props

### SlashCommandMenu Props

```typescript
interface SlashCommandMenuProps {
  position: { top: number; left: number };  // Absolute position
  onSelect: (command: SlashCommand) => void;  // Command selection callback
  onClose: () => void;  // Close menu callback
}
```

### FormattingToolbar Props

```typescript
interface FormattingToolbarProps {
  position: { top: number; left: number };  // Absolute position
  onFormat: (format: string, value?: string) => void;  // Format callback
  onClose: () => void;  // Close toolbar callback
}
```

### OutlinerEditor Props

```typescript
interface OutlinerEditorProps {
  initialBlocks?: Block[];  // Starting blocks
  onChange: (blocks: Block[]) => void;  // Block change callback
  placeholder?: string;  // Placeholder text
}
```

## CSS Styling

### Menu Styling

```css
/* SlashCommandMenu */
.fixed            /* Fixed positioning */
.bg-white         /* White background */
.rounded-lg       /* Rounded corners */
.shadow-xl        /* Large shadow */
.border           /* Gray border */
.z-50             /* High z-index */
.min-w-[280px]    /* Minimum width */

/* Menu items */
.hover:bg-blue-50  /* Hover effect */
.transition-colors /* Smooth transition */
```

### Toolbar Styling

```css
/* FormattingToolbar */
.fixed            /* Fixed positioning */
.flex gap-1       /* Horizontal layout */
.p-2              /* Padding */
.z-50             /* High z-index */

/* Color pickers */
.hidden group-hover:block  /* Show on hover */
.absolute top-full         /* Below button */
```

## Performance Optimizations

### Conditional Rendering

```typescript
{slashMenuPosition && (
  <SlashCommandMenu ... />
)}

{toolbarPosition && (
  <FormattingToolbar ... />
)}
```

Only renders when needed, saves memory and processing.

### Event Delegation

All keyboard events handled by OutlinerEditor, not individual blocks.

### Batched Updates

```typescript
const newBlocks = [...blocks];
newBlocks[blockIndex] = { ...block, content: newContent };
setBlocks(newBlocks);  // Single state update
```

## Error Handling

### Null Checks

```typescript
if (!selectedText) return;  // Guard clause

const blockIndex = blocks.findIndex(...);
if (blockIndex === -1) return;  // Block not found

const textarea = inputRefs.current[blockId];
if (!textarea) return;  // Ref not available
```

### Boundary Checks

```typescript
// Only show slash menu at valid positions
if (cursorPos === 0 || block.content[cursorPos - 1] === ' ') {
  // Show menu
}
```

## Integration Points

### With NoteForm

```typescript
// NoteForm.tsx
<OutlinerEditor
  initialBlocks={blocks}
  onChange={setBlocks}
  placeholder="Start typing..."
/>
```

OutlinerEditor is a controlled component - blocks managed by parent.

### With Backend

```typescript
// Blocks serialized to JSON for storage
const contentJSON = JSON.stringify(blocks);

// Sent to backend
await createNote.mutateAsync({
  content: contentJSON,  // Contains formatted text
  ...
});
```

## Testing Strategy

### Unit Tests

```typescript
// Test format application
test('applyFormatting wraps text in bold markers', () => {
  const result = applyFormatting('bold', 'hello');
  expect(result).toBe('**hello**');
});
```

### Integration Tests

```typescript
// Test slash menu interaction
test('slash menu appears on / key', () => {
  const { getByRole } = render(<OutlinerEditor ... />);
  const textarea = getByRole('textbox');

  fireEvent.keyDown(textarea, { key: '/' });

  expect(screen.getByText('Bold')).toBeInTheDocument();
});
```

### E2E Tests

```typescript
// Test full formatting flow
test('user can bold text with keyboard shortcut', async () => {
  await page.type('textarea', 'hello world');
  await page.keyboard.down('Shift');
  await page.keyboard.press('ArrowLeft', { count: 5 });
  await page.keyboard.up('Shift');
  await page.keyboard.press('Meta+KeyB');

  const content = await page.$eval('textarea', el => el.value);
  expect(content).toBe('hello **world**');
});
```

## Debugging Tips

### Check State

```typescript
console.log('Slash menu position:', slashMenuPosition);
console.log('Selected text:', selectedText);
console.log('Current blocks:', blocks);
```

### Check Events

```typescript
console.log('Key pressed:', e.key);
console.log('Meta key:', e.metaKey);
console.log('Selection:', textarea.selectionStart, textarea.selectionEnd);
```

### Check DOM

```typescript
console.log('Textarea rect:', textarea.getBoundingClientRect());
console.log('Selection rect:', window.getSelection()?.getRangeAt(0).getBoundingClientRect());
```

---

**Last Updated**: December 15, 2025
