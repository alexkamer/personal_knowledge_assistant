/**
 * TagFilter component for filtering notes by tags - Dropdown version.
 */

import React, { useState, useRef, useEffect } from 'react';
import { X, ChevronDown, Filter } from 'lucide-react';
import { useTags } from '../../hooks/useTags';

interface TagFilterProps {
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
}

export const TagFilter: React.FC<TagFilterProps> = ({ selectedTags, onTagsChange }) => {
  const { data: allTags, isLoading } = useTags();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleToggleTag = (tagName: string) => {
    if (selectedTags.includes(tagName)) {
      onTagsChange(selectedTags.filter((t) => t !== tagName));
    } else {
      onTagsChange([...selectedTags, tagName]);
    }
  };

  const handleClearAll = () => {
    onTagsChange([]);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-3">
        <p className="text-sm text-stone-500">Loading tags...</p>
      </div>
    );
  }

  if (!allTags || allTags.length === 0) {
    return null; // Don't show filter if no tags exist
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-white border-2 border-stone-300 rounded-lg hover:border-blue-400 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-stone-600" />
          <span className="text-sm font-medium text-stone-700">
            {selectedTags.length > 0 ? `${selectedTags.length} tag${selectedTags.length !== 1 ? 's' : ''} selected` : 'Filter by tags'}
          </span>
        </div>
        <ChevronDown
          size={16}
          className={`text-stone-600 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border border-stone-200 z-20 max-h-80 overflow-y-auto">
          {/* Header */}
          <div className="flex justify-between items-center px-4 py-3 border-b border-stone-200 sticky top-0 bg-white">
            <h3 className="font-medium text-stone-900 text-sm">Select Tags</h3>
            {selectedTags.length > 0 && (
              <button
                onClick={handleClearAll}
                className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <X size={12} />
                Clear all
              </button>
            )}
          </div>

          {/* Tag List */}
          <div className="p-2">
            {allTags.map((tag) => {
              const isSelected = selectedTags.includes(tag.name);
              return (
                <label
                  key={tag.id}
                  className={`flex items-center justify-between p-2.5 rounded cursor-pointer transition-colors ${
                    isSelected ? 'bg-blue-50' : 'hover:bg-stone-50'
                  }`}
                >
                  <div className="flex items-center gap-2 flex-1">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleTag(tag.name)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                    <span className={`text-sm ${isSelected ? 'font-medium text-blue-700' : 'text-stone-700'}`}>
                      {tag.name}
                    </span>
                  </div>
                  <span className="text-xs text-stone-500">({tag.note_count})</span>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* Selected Tags Pills (below dropdown) */}
      {selectedTags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {selectedTags.map((tagName) => (
            <span
              key={tagName}
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full"
            >
              {tagName}
              <button
                onClick={() => handleToggleTag(tagName)}
                className="hover:bg-blue-200 rounded-full p-0.5 transition-colors"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
