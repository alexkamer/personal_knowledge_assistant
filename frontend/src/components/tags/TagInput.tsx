/**
 * TagInput component with autocomplete.
 */

import { useState, useRef } from 'react';
import { X } from 'lucide-react';
import { useTags } from '../../hooks/useTags';

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  disabled?: boolean;
}

export const TagInput: React.FC<TagInputProps> = ({ value, onChange, disabled = false }) => {
  const [inputValue, setInputValue] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: allTags } = useTags();

  // Filter suggestions based on input
  const suggestions = allTags
    ?.filter(
      (tag) =>
        tag.name.toLowerCase().includes(inputValue.toLowerCase()) &&
        !value.includes(tag.name)
    )
    .slice(0, 5) || [];

  const handleAddTag = (tagName: string) => {
    const normalized = tagName.trim().toLowerCase();
    if (normalized && !value.includes(normalized)) {
      onChange([...value, normalized]);
      setInputValue('');
      setShowSuggestions(false);
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onChange(value.filter((tag) => tag !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (inputValue.trim()) {
        handleAddTag(inputValue);
      }
    } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
      // Remove last tag on backspace if input is empty
      handleRemoveTag(value[value.length - 1]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    setShowSuggestions(e.target.value.length > 0);
  };

  const handleInputBlur = () => {
    // Delay to allow clicking on suggestions
    setTimeout(() => setShowSuggestions(false), 200);
  };

  return (
    <div className="relative">
      <label htmlFor="tags" className="block text-sm font-medium text-stone-700 mb-1">
        Tags
      </label>

      {/* Tag display and input */}
      <div
        className={`flex flex-wrap gap-2 p-2 border border-stone-300 rounded-md min-h-[42px] ${
          disabled ? 'bg-stone-100 cursor-not-allowed' : 'bg-white'
        }`}
        onClick={() => !disabled && inputRef.current?.focus()}
      >
        {/* Selected tags */}
        {value.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-sm rounded"
          >
            {tag}
            {!disabled && (
              <button
                type="button"
                onClick={() => handleRemoveTag(tag)}
                className="hover:text-blue-900"
                aria-label={`Remove tag ${tag}`}
              >
                <X size={14} />
              </button>
            )}
          </span>
        ))}

        {/* Input */}
        <input
          ref={inputRef}
          type="text"
          id="tags"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => inputValue && setShowSuggestions(true)}
          onBlur={handleInputBlur}
          disabled={disabled}
          placeholder={value.length === 0 ? 'Add tags...' : ''}
          className="flex-1 min-w-[120px] outline-none bg-transparent disabled:cursor-not-allowed"
        />
      </div>

      {/* Autocomplete suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-stone-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
          {suggestions.map((tag) => (
            <button
              key={tag.id}
              type="button"
              onClick={() => handleAddTag(tag.name)}
              className="w-full text-left px-3 py-2 hover:bg-stone-100 flex justify-between items-center"
            >
              <span>{tag.name}</span>
              <span className="text-xs text-stone-500">({tag.note_count} notes)</span>
            </button>
          ))}
        </div>
      )}

      <p className="mt-1 text-xs text-stone-500">
        Press Enter to add a tag. Click X to remove.
      </p>
    </div>
  );
};
