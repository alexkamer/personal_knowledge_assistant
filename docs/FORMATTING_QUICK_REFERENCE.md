# Formatting Quick Reference

## Keyboard Shortcuts

| Shortcut | Action | Result |
|----------|--------|--------|
| `Cmd+B` or `Ctrl+B` | Bold selected text | `**text**` |
| `Cmd+I` or `Ctrl+I` | Italic selected text | `*text*` |
| `Cmd+U` or `Ctrl+U` | Underline selected text | `__text__` |
| `/` | Open slash command menu | Shows formatting options |
| `Enter` | New block | Creates new bullet point |
| `Tab` | Indent block | Increases indentation |
| `Shift+Tab` | Outdent block | Decreases indentation |
| `Backspace` (on empty) | Delete block | Removes empty bullet |
| `↑` / `↓` | Navigate blocks | Moves cursor between blocks |

## Slash Commands

Type `/` at the start of a line or after a space to open the menu:

| Command | Icon | Description | Result |
|---------|------|-------------|--------|
| Bold | **B** | Make text bold | Inserts `****` |
| Italic | *I* | Make text italic | Inserts `**` |
| Underline | U | Underline text | Inserts `____` |
| Heading | T | Large heading | Inserts `# ` |
| Text Color | 🎨 | Change text color | Opens color picker |
| Highlight | ✏️ | Highlight background | Opens highlight picker |

## Text Selection Toolbar

Select text with your mouse to show the toolbar:

### Quick Format Buttons

- **Bold** - Makes text bold
- **Italic** - Makes text italic
- **Underline** - Underlines text

### Color Options (hover over palette icon)

**Text Colors**:
- 🔴 Red (#ef4444)
- 🟠 Orange (#f97316)
- 🟡 Yellow (#eab308)
- 🟢 Green (#22c55e)
- 🔵 Blue (#3b82f6)
- 🟣 Purple (#a855f7)
- 🩷 Pink (#ec4899)
- ⚫ Gray (#6b7280)

**Highlights**:
- 🟡 Yellow (#fef08a)
- 🟢 Green (#bbf7d0)
- 🔵 Blue (#bfdbfe)
- 🟣 Purple (#e9d5ff)
- 🩷 Pink (#fbcfe8)
- 🔴 Red (#fecaca)

## Formatting Syntax

### Markdown Formats

```markdown
**bold text**
*italic text*
__underlined text__
# Heading text
```

### HTML Color Formats

```html
<span style="color: #ef4444">colored text</span>
<span style="background-color: #fef08a">highlighted text</span>
```

## Usage Examples

### Example 1: Bold with Keyboard

1. Type: `This is important`
2. Select `important` with mouse or Shift+Arrow keys
3. Press `Cmd+B` (Mac) or `Ctrl+B` (Windows/Linux)
4. Result: `This is **important**`

### Example 2: Color with Toolbar

1. Type: `Red alert`
2. Select `Red` with mouse
3. Toolbar appears above selection
4. Click palette icon 🎨
5. Hover and click red color
6. Result: `<span style="color: #ef4444">Red</span> alert`

### Example 3: Highlight with Slash Command

1. Type `/`
2. Menu appears
3. Click "Highlight"
4. Select text you want to highlight
5. Use toolbar to pick color

## Tips & Tricks

### Multiple Formats

You can combine formats:
```markdown
**_bold and italic_**
<span style="color: #ef4444">**colored and bold**</span>
```

### Quick Navigation

- Use `↑` and `↓` at start/end of line to move between blocks
- Use `Enter` to quickly create new blocks
- Use `Tab` to organize into hierarchies

### Slash Command Position

The `/` only triggers the menu when:
- At the very start of a line
- After a space character

This prevents accidental menu triggers when typing URLs or fractions.

### Closing Menus

- Click outside the menu
- Press `Esc` (future enhancement)
- Select a command
- Start typing (for slash menu)

## Common Issues

### Slash menu not appearing?

✅ Check cursor position - must be at start or after space
✅ Make sure you're focused in the text area

### Toolbar not showing?

✅ Use mouse to select text (keyboard selection doesn't trigger toolbar)
✅ Try using keyboard shortcuts instead (`Cmd+B`, etc.)

### Formats not rendering visually?

ℹ️ Currently formats are stored as markdown/HTML text
ℹ️ Visual rendering is a planned future enhancement
ℹ️ You'll see the raw markdown syntax for now

## What's Stored

When you save a note, the formatting is stored as:

```json
{
  "id": "block_123",
  "content": "This is **bold** and <span style=\"color: #ef4444\">red</span>",
  "indent": 0
}
```

The content includes both markdown and HTML formatting inline.

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)

Keyboard shortcuts work with:
- ✅ `Cmd` key on macOS
- ✅ `Ctrl` key on Windows/Linux

## Accessibility

- All buttons have `title` attributes for tooltips
- Keyboard shortcuts work alongside mouse interactions
- Visual indicators for active states
- High contrast colors for visibility

## Performance

- Menus only render when triggered
- No performance impact on typing
- Efficient state updates
- Works smoothly with 100+ blocks

## Related Documentation

- [Full Formatting System Docs](./FORMATTING_SYSTEM.md)
- [Architecture Details](./FORMATTING_ARCHITECTURE.md)
- [Project Overview](../.claude/CLAUDE.md)

---

**Version**: 1.0.0
**Last Updated**: December 15, 2025
**For**: Personal Knowledge Assistant
