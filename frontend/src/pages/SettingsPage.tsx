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
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6 border-b border-stone-200 pb-4">
          <Settings size={28} className="text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-stone-800">Settings</h1>
            <p className="text-sm text-stone-600">Configure your AI assistant</p>
          </div>
        </div>

        {/* Model Selection Section */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-stone-800 mb-2">AI Model Selection</h2>
          <p className="text-sm text-stone-600 mb-4">
            Choose which local LLM model to use for answering your questions. Each model has different trade-offs between speed and capability.
          </p>

          <div className="space-y-3">
            {AVAILABLE_MODELS.map((model) => (
              <div
                key={model.id}
                onClick={() => handleModelSelect(model.id)}
                className={`relative p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedModel === model.id
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-stone-200 hover:border-stone-300 hover:bg-stone-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-stone-900">{model.name}</h3>
                      {selectedModel === model.id && (
                        <CheckCircle size={20} className="text-blue-600" />
                      )}
                    </div>
                    <p className="text-sm text-stone-600 mt-1">{model.description}</p>
                    <div className="flex gap-4 mt-2">
                      <span className="text-xs text-stone-500">
                        <strong>Size:</strong> {model.size}
                      </span>
                      <span className="text-xs text-stone-500">
                        <strong>Speed:</strong> {model.speed}
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
          <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-md text-green-800">
            <CheckCircle size={18} />
            <span className="text-sm font-medium">Settings saved successfully</span>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">About Local Models</h3>
          <p className="text-sm text-blue-800">
            All models run locally on your machine using Ollama. Your data never leaves your computer, ensuring complete privacy. Model changes take effect immediately for new conversations.
          </p>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
