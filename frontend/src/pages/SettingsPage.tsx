/**
 * Settings page for configuring the application.
 */
import { useState, useEffect } from 'react';
import { Settings, CheckCircle } from 'lucide-react';

const AVAILABLE_MODELS = [
  {
    id: 'qwen2.5:14b',
    name: 'Qwen 2.5 14B',
    description: 'Best reasoning and complex queries (Primary)',
    size: '14B parameters',
    speed: 'Medium',
  },
  {
    id: 'phi4:14b',
    name: 'Phi-4 14B',
    description: 'Optimized for reasoning tasks',
    size: '14B parameters',
    speed: 'Medium',
  },
  {
    id: 'llama3.2:3b',
    name: 'Llama 3.2 3B',
    description: 'Fast responses for simple queries',
    size: '3B parameters',
    speed: 'Fast',
  },
];

function SettingsPage() {
  const [selectedModel, setSelectedModel] = useState<string>('qwen2.5:14b');
  const [saved, setSaved] = useState(false);

  // Load saved model preference from localStorage
  useEffect(() => {
    const savedModel = localStorage.getItem('preferred_model');
    if (savedModel) {
      setSelectedModel(savedModel);
    }
  }, []);

  const handleModelSelect = (modelId: string) => {
    setSelectedModel(modelId);
    localStorage.setItem('preferred_model', modelId);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border border-gray-700 rounded-lg p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6 border-b border-gray-700 pb-4">
          <Settings size={20} className="text-gray-400" />
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-white">Settings</h1>
            <p className="text-xs text-gray-400">Configure your AI assistant</p>
          </div>
        </div>

        {/* Model Selection Section */}
        <div className="mb-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-3">AI Model Selection</h2>
          <p className="text-xs text-gray-400 mb-4">
            Choose which local LLM model to use for answering your questions.
          </p>

          <div className="space-y-2">
            {AVAILABLE_MODELS.map((model) => (
              <div
                key={model.id}
                onClick={() => handleModelSelect(model.id)}
                className={`relative p-4 border rounded-md cursor-pointer transition-all duration-150 ${
                  selectedModel === model.id
                    ? 'border-gray-900 dark:border-white bg-gray-900 dark:bg-white text-white dark:text-gray-900'
                    : 'border-gray-200 dark:border-gray-700 bg-gray-900/80 backdrop-blur-md hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className={`text-sm font-semibold ${selectedModel === model.id ? 'text-white dark:text-gray-900' : 'text-white'}`}>
                        {model.name}
                      </h3>
                      {selectedModel === model.id && (
                        <CheckCircle size={16} className={selectedModel === model.id ? 'text-white dark:text-gray-900' : ''} />
                      )}
                    </div>
                    <p className={`text-xs mt-1 ${selectedModel === model.id ? 'text-gray-200 dark:text-gray-700' : 'text-gray-400'}`}>
                      {model.description}
                    </p>
                    <div className="flex gap-4 mt-2">
                      <span className={`text-xs ${selectedModel === model.id ? 'text-gray-300 dark:text-gray-600' : 'text-gray-500 dark:text-gray-500'}`}>
                        {model.size} • {model.speed}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Save Confirmation */}
        {saved && (
          <div className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md text-green-800 dark:text-green-400">
            <CheckCircle size={16} />
            <span className="text-xs font-medium">Settings saved successfully</span>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900/50 border border-gray-700 rounded-md">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">About Local Models</h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            All models run locally on your machine using Ollama. Your data never leaves your computer, ensuring complete privacy.
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
