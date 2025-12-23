# Keyboard Shortcuts Reference

Complete guide to all keyboard shortcuts in the Personal Knowledge Assistant.

## Global Shortcuts (Work Everywhere)

| Shortcut | Action | Context |
|----------|--------|---------|
| `Cmd+K` | Open Command Palette | Notes page |

## Command Palette (Cmd+K)

Once the Command Palette is open:

| Shortcut | Action |
|----------|--------|
| `↑` / `↓` | Navigate results |
| `Enter` | Select item |
| `Escape` | Close palette |
| Type to search | Filter results |

## Note Editor - Text Formatting

| Shortcut | Action |
|----------|--------|
| `Cmd+B` | **Bold** |
| `Cmd+I` | *Italic* |
| `Cmd+U` | Underline |
| `Cmd+Shift+X` | ~~Strikethrough~~ |
| `Cmd+E` | `Inline code` |
| `Cmd+Shift+K` | Insert/edit link |

## Note Editor - Structure

| Shortcut | Action |
|----------|--------|
| `Enter` | New line |
| `Tab` | Indent (increase nesting) |
| `Shift+Tab` | Outdent (decrease nesting) |
| `-` + `Space` | Create bullet list |
| `1.` + `Space` | Create numbered list |
| `/` | Open slash command menu |

## Note Editor - Slash Commands

Type `/` to open the formatting menu:

| Command | Result |
|---------|--------|
| `/h1` | Heading 1 |
| `/h2` | Heading 2 |
| `/h3` | Heading 3 |
| `/bullet` | Bullet list |
| `/number` | Numbered list |
| `/code` | Code block |
| `/quote` | Quote block |
| `/table` | Insert customizable table |

## Note Editor - Tables

| Shortcut | Action |
|----------|--------|
| `/table` | Open table insertion modal |
| `Tab` | Navigate to next cell |
| `Shift+Tab` | Navigate to previous cell |
| `Right-click` on cell | Open table context menu |

**Context Menu Options:**
- Insert row above/below
- Insert column left/right
- Clear cell contents
- Delete row/column
- Delete entire table

## Note Editor - Wiki Links

| Shortcut | Action |
|----------|--------|
| `[[` | Create wiki link to another note |
| `[[Note Title]]` | Link to note with autocomplete |
| `Click` on `[[link]]` | Navigate to linked note |

## Note Editor - Images

| Action | How to |
|--------|--------|
| Paste image | `Cmd+V` with image in clipboard |
| Drag & drop | Drag image file into editor |
| Resize image | Click and drag image corners |

## Note Management

| Shortcut | Action | Where |
|----------|--------|-------|
| `Cmd+K` then type | Search notes | Notes page |
| `Cmd+K` → "Create new note" | New note | Notes page |
| Click note in sidebar | Open note | Notes page |

## Browser/System Shortcuts (Not Overridden)

These standard shortcuts still work:

| Shortcut | Action |
|----------|--------|
| `Cmd+Z` | Undo |
| `Cmd+Shift+Z` | Redo |
| `Cmd+A` | Select all |
| `Cmd+C` | Copy |
| `Cmd+X` | Cut |
| `Cmd+V` | Paste |
| `Cmd+F` | Find in page (browser default) |

## Shortcuts by Use Case

### Quick Note Creation
1. `Cmd+K` - Open Command Palette
2. Type "create" or just press `Enter` (first option)
3. Start typing your note

### Navigate Between Notes
1. `Cmd+K` - Open Command Palette
2. Type note title (fuzzy search works!)
3. `Enter` to open note

### Format While Writing
- **Bold text**: Select text → `Cmd+B`
- **Add link**: Select text → `Cmd+Shift+K` → paste URL → `Enter`
- **Create list**: Type `-` + `Space` at start of line

### Connect Notes Together
1. Type `[[` in the editor
2. Start typing note title
3. Select from autocomplete
4. Link is created!

## Shortcut Conflicts - RESOLVED ✅

| Shortcut | Old Assignment | New Assignment | Reason for Change |
|----------|----------------|----------------|-------------------|
| `Cmd+K` | Insert link | Command Palette | Command Palette is more universal |
| `Cmd+Shift+K` | - | Insert link | Standard in VS Code, Sublime Text |

## Platform Differences

**macOS**: Uses `Cmd` (⌘) key
**Windows/Linux**: Uses `Ctrl` key

All shortcuts listed use `Cmd` for macOS. On Windows/Linux, replace `Cmd` with `Ctrl`:
- `Cmd+K` → `Ctrl+K`
- `Cmd+B` → `Ctrl+B`
- etc.

## Tips for Power Users

1. **Learn Command Palette First**
   - `Cmd+K` is your best friend
   - Fuzzy search means you don't need exact matches
   - Recent notes appear first (no query needed)

2. **Use Slash Commands for Speed**
   - Type `/` instead of clicking toolbar buttons
   - Faster than reaching for mouse
   - Keyboard navigation with arrow keys

3. **Master Wiki Links**
   - `[[` triggers autocomplete
   - Build a connected knowledge base
   - Backlinks show automatically

4. **Keyboard-First Workflow**
   ```
   1. Cmd+K → find note
   2. Start typing
   3. [[link]] to connect ideas
   4. Cmd+B/I for emphasis
   5. Cmd+K → next note
   ```

## Future Shortcuts (Planned)

These shortcuts may be added in future updates:

| Shortcut | Planned Action |
|----------|----------------|
| `Cmd+O` | Quick Switcher (notes only) |
| `Cmd+D` | Daily note |
| `Cmd+/` or `?` | Show keyboard shortcuts modal |
| `Cmd+P` | Command Palette (alternate) |
| `Cmd+\` | Toggle sidebar |

## Customization

Currently, keyboard shortcuts are **not customizable**. They follow industry standards (VS Code, Obsidian, Notion) to reduce learning curve.

If you need custom shortcuts, please submit a feature request on GitHub.

---

## Quick Reference Card

Print this section for quick access:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PERSONAL KNOWLEDGE ASSISTANT - SHORTCUTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  GLOBAL
  ├─ Cmd+K          Command Palette

  FORMATTING
  ├─ Cmd+B          Bold
  ├─ Cmd+I          Italic
  ├─ Cmd+U          Underline
  ├─ Cmd+Shift+X    Strikethrough
  ├─ Cmd+E          Inline code
  └─ Cmd+Shift+K    Insert link

  STRUCTURE
  ├─ Tab            Indent
  ├─ Shift+Tab      Outdent
  ├─ /              Slash menu
  └─ [[             Wiki link

  COMMAND PALETTE (Cmd+K)
  ├─ ↑↓             Navigate
  ├─ Enter          Select
  └─ Escape         Close

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**Last Updated**: 2025-12-19
**Version**: 1.0
**Conflicts Resolved**: Cmd+K now exclusively for Command Palette
