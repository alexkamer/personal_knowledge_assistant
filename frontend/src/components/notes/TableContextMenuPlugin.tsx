/**
 * Table Context Menu Plugin
 * Right-click menu for table operations (add/delete rows/columns)
 */
import { useEffect, useState, useCallback } from 'react';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
  $getSelection,
  $isRangeSelection,
  $createParagraphNode,
  COMMAND_PRIORITY_LOW,
} from 'lexical';
import {
  $isTableNode,
  $isTableCellNode,
  TableCellNode,
  INSERT_TABLE_COMMAND,
  $getTableColumnIndexFromTableCellNode,
  $getTableRowIndexFromTableCellNode,
  $insertTableColumn__EXPERIMENTAL,
  $insertTableRow__EXPERIMENTAL,
  $deleteTableColumn__EXPERIMENTAL,
  $deleteTableRow__EXPERIMENTAL,
} from '@lexical/table';
import { Plus, Trash2, Eraser, Copy, Table as TableIcon } from 'lucide-react';

interface MenuPosition {
  x: number;
  y: number;
}

export function TableContextMenuPlugin() {
  const [editor] = useLexicalComposerContext();
  const [menuPosition, setMenuPosition] = useState<MenuPosition | null>(null);
  const [tableCellNode, setTableCellNode] = useState<TableCellNode | null>(null);
  const [isHeaderCell, setIsHeaderCell] = useState<boolean>(false);
  const [cellPosition, setCellPosition] = useState<{ row: number; col: number } | null>(null);

  const handleContextMenu = useCallback(
    (event: MouseEvent) => {
      editor.getEditorState().read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) return;

        // Traverse up the tree to find the table cell node
        let node = selection.anchor.getNode();
        let cellNode = null;

        // Keep going up the parent chain until we find a table cell or reach the root
        while (node && !cellNode) {
          if ($isTableCellNode(node)) {
            cellNode = node;
            break;
          }
          node = node.getParent();
        }

        if (cellNode && $isTableCellNode(cellNode)) {
          event.preventDefault();
          setMenuPosition({ x: event.clientX, y: event.clientY });
          setTableCellNode(cellNode);

          // Detect if this is a header cell by checking the tag type
          const domElement = editor.getElementByKey(cellNode.getKey());
          const isHeader = domElement?.tagName === 'TH';
          setIsHeaderCell(isHeader);

          // Get cell position
          const rowIndex = $getTableRowIndexFromTableCellNode(cellNode);
          const colIndex = $getTableColumnIndexFromTableCellNode(cellNode);
          setCellPosition({ row: rowIndex, col: colIndex });
        }
      });
    },
    [editor]
  );

  const handleClickOutside = useCallback(() => {
    setMenuPosition(null);
    setTableCellNode(null);
    setIsHeaderCell(false);
    setCellPosition(null);
  }, []);

  useEffect(() => {
    const editorElement = editor.getRootElement();
    if (!editorElement) return;

    editorElement.addEventListener('contextmenu', handleContextMenu);
    document.addEventListener('click', handleClickOutside);

    return () => {
      editorElement.removeEventListener('contextmenu', handleContextMenu);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [editor, handleContextMenu, handleClickOutside]);

  const insertRowAbove = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      $insertTableRow__EXPERIMENTAL(false);
    });
    setMenuPosition(null);
  };

  const insertRowBelow = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      $insertTableRow__EXPERIMENTAL(true);
    });
    setMenuPosition(null);
  };

  const insertColumnLeft = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      $insertTableColumn__EXPERIMENTAL(false);
    });
    setMenuPosition(null);
  };

  const insertColumnRight = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      $insertTableColumn__EXPERIMENTAL(true);
    });
    setMenuPosition(null);
  };

  const deleteRow = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      $deleteTableRow__EXPERIMENTAL();
    });
    setMenuPosition(null);
  };

  const deleteColumn = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      $deleteTableColumn__EXPERIMENTAL();
    });
    setMenuPosition(null);
  };

  const clearCell = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      if ($isTableCellNode(tableCellNode)) {
        // Clear all children of the cell
        const children = tableCellNode.getChildren();
        children.forEach(child => child.remove());
        // Add empty paragraph
        const paragraph = $createParagraphNode();
        tableCellNode.append(paragraph);
      }
    });
    setMenuPosition(null);
  };

  const deleteTable = () => {
    if (!tableCellNode) return;
    editor.update(() => {
      if ($isTableCellNode(tableCellNode)) {
        // Find the table node and remove it
        let node = tableCellNode.getParent();
        while (node && !$isTableNode(node)) {
          node = node.getParent();
        }
        if (node && $isTableNode(node)) {
          node.remove();
        }
      }
    });
    setMenuPosition(null);
  };

  if (!menuPosition) return null;

  return (
    <div
      className="fixed bg-gray-900 text-white rounded-lg shadow-xl border border-gray-700 z-50 py-1 min-w-[200px]"
      style={{ top: menuPosition.y, left: menuPosition.x }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Cell type indicator */}
      {isHeaderCell && (
        <div className="px-4 py-2 text-xs font-medium text-blue-400 bg-blue-900/30 border-b border-gray-700">
          Header Cell (Row {cellPosition?.row}, Col {cellPosition?.col})
        </div>
      )}

      <div className="px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide">
        Insert
      </div>

      {/* For header cells, show limited insertion options */}
      {isHeaderCell ? (
        <>
          {cellPosition?.row === 0 ? (
            // Top row header - only allow inserting rows below
            <ContextMenuItem
              label="Row below (after headers)"
              icon={<Plus size={16} />}
              onClick={insertRowBelow}
            />
          ) : (
            // Left column header - only allow inserting columns right
            <ContextMenuItem
              label="Column right (after headers)"
              icon={<Plus size={16} />}
              onClick={insertColumnRight}
            />
          )}
        </>
      ) : (
        // Data cells - show all insertion options
        <>
          <ContextMenuItem
            label="Row above"
            icon={<Plus size={16} />}
            onClick={insertRowAbove}
          />
          <ContextMenuItem
            label="Row below"
            icon={<Plus size={16} />}
            onClick={insertRowBelow}
          />
          <ContextMenuItem
            label="Column left"
            icon={<Plus size={16} />}
            onClick={insertColumnLeft}
          />
          <ContextMenuItem
            label="Column right"
            icon={<Plus size={16} />}
            onClick={insertColumnRight}
          />
        </>
      )}

      <div className="border-t border-gray-700 my-1" />

      <div className="px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide">
        Cell
      </div>
      <ContextMenuItem
        label="Clear cell"
        icon={<Eraser size={16} />}
        onClick={clearCell}
      />

      <div className="border-t border-gray-700 my-1" />

      <div className="px-2 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide">
        Delete
      </div>
      <ContextMenuItem
        label="Delete row"
        icon={<Trash2 size={16} />}
        onClick={deleteRow}
        danger
      />
      <ContextMenuItem
        label="Delete column"
        icon={<Trash2 size={16} />}
        onClick={deleteColumn}
        danger
      />
      <ContextMenuItem
        label="Delete table"
        icon={<TableIcon size={16} />}
        onClick={deleteTable}
        danger
      />
    </div>
  );
}

interface ContextMenuItemProps {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  danger?: boolean;
}

function ContextMenuItem({ label, icon, onClick, danger }: ContextMenuItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors text-left ${
        danger
          ? 'hover:bg-red-600/20 text-red-400'
          : 'hover:bg-gray-800 text-gray-200'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
