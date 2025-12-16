/**
 * TagFilter component for filtering notes by tags.
 */

import React from 'react';
import { X } from 'lucide-react';
import { useTags } from '../../hooks/useTags';

interface TagFilterProps {
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
}

export const TagFilter: React.FC<TagFilterProps> = ({ selectedTags, onTagsChange }) => {
  const { data: allTags, isLoading } = useTags();

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

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <p className="text-sm text-gray-500">Loading tags...</p>
      </div>
    );
  }

  if (!allTags || allTags.length === 0) {
    return null; // Don't show filter if no tags exist
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-medium text-gray-900">Filter by Tags</h3>
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

      <div className="space-y-2">
        {allTags.map((tag) => {
          const isSelected = selectedTags.includes(tag.name);
          return (
            <label
              key={tag.id}
              className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2 flex-1">
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => handleToggleTag(tag.name)}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <span className={`text-sm ${isSelected ? 'font-medium text-blue-700' : 'text-gray-700'}`}>
                  {tag.name}
                </span>
              </div>
              <span className="text-xs text-gray-500">({tag.note_count})</span>
            </label>
          );
        })}
      </div>

      {selectedTags.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            Showing notes with {selectedTags.length} tag{selectedTags.length !== 1 ? 's' : ''}
          </p>
        </div>
      )}
    </div>
  );
};
