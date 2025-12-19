/**
 * Advanced search component for documents with debouncing
 */
import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';

interface DocumentsSearchProps {
  onSearch: (query: string) => void;
  initialValue?: string;
  placeholder?: string;
}

export function DocumentsSearch({ onSearch, initialValue = '', placeholder = 'Search documents...' }: DocumentsSearchProps) {
  const [value, setValue] = useState(initialValue);

  // Sync with initialValue from URL
  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch(value);
    }, 300);

    return () => clearTimeout(timer);
  }, [value, onSearch]);

  return (
    <div className="relative group">
      <Search
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-primary-400 transition-colors"
        size={18}
      />
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="
          w-full pl-10 pr-10 py-2.5
          glass glass-hover
          rounded-lg
          text-white placeholder-gray-500
          focus:outline-none focus:ring-2 focus:ring-primary-500/50
          transition-all duration-200
        "
      />
      {value && (
        <button
          onClick={() => setValue('')}
          className="
            absolute right-3 top-1/2 -translate-y-1/2
            text-gray-400 hover:text-white
            transition-colors spring-scale
          "
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}
