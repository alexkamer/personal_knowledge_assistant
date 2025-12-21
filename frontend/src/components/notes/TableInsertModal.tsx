/**
 * Table Insert Modal
 * Modal for customizing table dimensions before insertion
 */
import { useState } from 'react';
import { X, Table as TableIcon } from 'lucide-react';

interface TableInsertModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInsert: (rows: number, columns: number, includeHeaderRow: boolean, includeHeaderColumn: boolean) => void;
}

export function TableInsertModal({ isOpen, onClose, onInsert }: TableInsertModalProps) {
  const [rows, setRows] = useState(3);
  const [columns, setColumns] = useState(3);
  const [includeHeaderRow, setIncludeHeaderRow] = useState(true);
  const [includeHeaderColumn, setIncludeHeaderColumn] = useState(false);

  if (!isOpen) return null;

  const handleInsert = () => {
    onInsert(rows, columns, includeHeaderRow, includeHeaderColumn);
    onClose();
    // Reset to defaults
    setRows(3);
    setColumns(3);
    setIncludeHeaderRow(true);
    setIncludeHeaderColumn(false);
  };

  const handleCancel = () => {
    onClose();
    // Reset to defaults
    setRows(3);
    setColumns(3);
    setIncludeHeaderRow(true);
    setIncludeHeaderColumn(false);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={handleCancel}
    >
      <div
        className="w-full max-w-md rounded-lg border border-gray-700 bg-gray-900 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-700 px-6 py-4">
          <div className="flex items-center gap-3">
            <TableIcon size={24} className="text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-100">
              Insert Table
            </h2>
          </div>
          <button
            onClick={handleCancel}
            className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-gray-300"
            title="Close (Esc)"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Rows Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">
              Number of Rows
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={rows}
              onChange={(e) => setRows(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
              className="w-full rounded-lg border border-gray-600 bg-gray-800 px-4 py-2 text-gray-100 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
            <p className="text-xs text-gray-500">Min: 1, Max: 20</p>
          </div>

          {/* Columns Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">
              Number of Columns
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={columns}
              onChange={(e) => setColumns(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
              className="w-full rounded-lg border border-gray-600 bg-gray-800 px-4 py-2 text-gray-100 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            />
            <p className="text-xs text-gray-500">Min: 1, Max: 10</p>
          </div>

          {/* Header Options */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
              Headers
            </p>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="include-header-row"
                checked={includeHeaderRow}
                onChange={(e) => setIncludeHeaderRow(e.target.checked)}
                className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
              />
              <label htmlFor="include-header-row" className="text-sm text-gray-300 cursor-pointer">
                Include header row (top row)
              </label>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="include-header-column"
                checked={includeHeaderColumn}
                onChange={(e) => setIncludeHeaderColumn(e.target.checked)}
                className="h-4 w-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500/50"
              />
              <label htmlFor="include-header-column" className="text-sm text-gray-300 cursor-pointer">
                Include header column (left column)
              </label>
            </div>
          </div>

          {/* Preview */}
          <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-3">
              Preview
            </p>
            <div className="overflow-auto">
              <table className="w-full border-collapse text-xs">
                <tbody>
                  {Array.from({ length: rows }).map((_, rowIndex) => (
                    <tr key={rowIndex}>
                      {Array.from({ length: columns }).map((_, colIndex) => {
                        const isHeaderRow = rowIndex === 0 && includeHeaderRow;
                        const isHeaderColumn = colIndex === 0 && includeHeaderColumn;
                        const isHeader = isHeaderRow || isHeaderColumn;

                        return (
                          <td
                            key={colIndex}
                            className={`border border-gray-600 px-2 py-1 text-center ${
                              isHeader
                                ? 'bg-gray-700 font-semibold text-gray-200'
                                : 'bg-gray-800/50 text-gray-400'
                            }`}
                          >
                            {isHeaderRow && isHeaderColumn ? '•' :
                             isHeaderRow ? `H${colIndex + 1}` :
                             isHeaderColumn ? `R${rowIndex}` : ''}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-gray-700 px-6 py-4">
          <button
            onClick={handleCancel}
            className="rounded-lg px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={handleInsert}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            Insert Table
          </button>
        </div>
      </div>
    </div>
  );
}
