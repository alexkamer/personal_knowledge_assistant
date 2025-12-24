/**
 * Wizard component for refining image generation prompts.
 * Guides users through questions to create detailed, high-quality prompts.
 */
import { useState, useMemo } from 'react';
import type { Question } from '@/types/promptRefinement';

interface PromptRefinementWizardProps {
  basicPrompt: string;
  category: string;
  questions: Question[];
  onComplete: (answers: Record<string, string>) => void;
  onCancel: () => void;
}

export function PromptRefinementWizard({
  basicPrompt,
  category,
  questions,
  onComplete,
  onCancel,
}: PromptRefinementWizardProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentStep, setCurrentStep] = useState(0);
  const [showPreview, setShowPreview] = useState(true);
  const [customInputs, setCustomInputs] = useState<Record<string, string>>({});

  const currentQuestion = questions[currentStep];
  const isLastQuestion = currentStep === questions.length - 1;
  const progress = ((currentStep + 1) / questions.length) * 100;

  // Get the actual answer (use custom input if "custom" is selected)
  const getActualAnswer = (questionId: string): string | undefined => {
    const answer = answers[questionId];
    if (answer === 'custom') {
      return customInputs[questionId];
    }
    return answer;
  };

  // Build live prompt preview
  const promptPreview = useMemo(() => {
    const parts = [basicPrompt];

    // For dynamically generated questions, simply append all answers
    // Skip the "extras" field as it's usually a text input we'll add at the end
    Object.keys(answers).forEach((questionId) => {
      if (questionId === 'extras') return; // Handle extras at the end

      const actualAnswer = getActualAnswer(questionId);
      if (actualAnswer && actualAnswer.trim()) {
        parts.push(actualAnswer.trim().toLowerCase());
      }
    });

    // Add user's extra details if provided (from free-text question)
    const extrasAnswer = getActualAnswer('extras');
    if (extrasAnswer && extrasAnswer.trim()) {
      parts.push(extrasAnswer);
    }

    parts.push('professional', 'high quality', 'detailed');

    return parts.join(', ');
  }, [basicPrompt, answers, customInputs]);

  const handleAnswer = (value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: value,
    }));

    // Clear custom input if switching away from "custom" option
    if (value !== 'custom') {
      setCustomInputs((prev) => {
        const updated = { ...prev };
        delete updated[currentQuestion.id];
        return updated;
      });
    }
  };

  const handleCustomInput = (value: string) => {
    setCustomInputs((prev) => ({
      ...prev,
      [currentQuestion.id]: value,
    }));
  };

  const handleNext = () => {
    if (isLastQuestion) {
      // Build final answers with custom inputs resolved
      const finalAnswers: Record<string, string> = {};
      Object.keys(answers).forEach((questionId) => {
        const actualAnswer = getActualAnswer(questionId);
        if (actualAnswer) {
          finalAnswers[questionId] = actualAnswer;
        }
      });
      onComplete(finalAnswers);
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSkip = () => {
    if (isLastQuestion) {
      onComplete(answers);
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const canProceed = () => {
    // Text questions can be empty (optional)
    if (currentQuestion.type === 'text') {
      return true;
    }
    // Single-select requires an answer
    const hasAnswer = answers[currentQuestion.id] !== undefined;

    // If "custom" is selected, require custom input
    if (hasAnswer && answers[currentQuestion.id] === 'custom') {
      return customInputs[currentQuestion.id]?.trim().length > 0;
    }

    return hasAnswer;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Refine Your Prompt</h2>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-white transition-colors"
              aria-label="Close wizard"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-gray-400">
              Original: <span className="text-white">{basicPrompt}</span>
            </p>
            <p className="text-xs text-gray-500">
              Category: <span className="text-gray-400 capitalize">{category}</span>
            </p>
          </div>

          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
              <span>
                Question {currentStep + 1} of {questions.length}
              </span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Live Prompt Preview */}
        {showPreview && (
          <div className="border-b border-gray-700 px-6 py-4 bg-gray-900/50">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-300">Enhanced Prompt Preview</h4>
              <button
                onClick={() => setShowPreview(false)}
                className="text-xs text-gray-500 hover:text-gray-400 transition-colors"
              >
                Hide
              </button>
            </div>
            <div className="bg-gray-950 rounded-lg p-3 border border-gray-700">
              <p className="text-sm text-gray-300 font-mono leading-relaxed">{promptPreview}</p>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              {Object.keys(answers).length} of {questions.length} questions answered
            </div>
          </div>
        )}

        {/* Show preview button if hidden */}
        {!showPreview && (
          <div className="border-b border-gray-700 px-6 py-2">
            <button
              onClick={() => setShowPreview(true)}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              ↓ Show Enhanced Prompt Preview
            </button>
          </div>
        )}

        {/* Question content */}
        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-lg font-medium text-white mb-4">{currentQuestion.question}</h3>

            {currentQuestion.type === 'single-select' && currentQuestion.options && (
              <div className="space-y-2">
                {currentQuestion.options.map((option) => (
                  <label
                    key={option}
                    className={`
                      flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all
                      ${
                        answers[currentQuestion.id] === option
                          ? 'border-indigo-500 bg-indigo-500/10'
                          : 'border-gray-700 bg-gray-900 hover:border-gray-600'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name={currentQuestion.id}
                      value={option}
                      checked={answers[currentQuestion.id] === option}
                      onChange={(e) => handleAnswer(e.target.value)}
                      className="w-4 h-4 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-gray-900"
                    />
                    <span className="ml-3 text-white">{option}</span>
                  </label>
                ))}

                {/* Custom option */}
                <div className="space-y-2">
                  <label
                    className={`
                      flex items-center p-4 rounded-lg border-2 cursor-pointer transition-all
                      ${
                        answers[currentQuestion.id] === 'custom'
                          ? 'border-indigo-500 bg-indigo-500/10'
                          : 'border-gray-700 bg-gray-900 hover:border-gray-600'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name={currentQuestion.id}
                      value="custom"
                      checked={answers[currentQuestion.id] === 'custom'}
                      onChange={(e) => handleAnswer(e.target.value)}
                      className="w-4 h-4 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-gray-900"
                    />
                    <span className="ml-3 text-white font-medium">✏️ Custom (write your own)</span>
                  </label>

                  {/* Custom input field (shown when "custom" is selected) */}
                  {answers[currentQuestion.id] === 'custom' && (
                    <div className="pl-8 pt-2">
                      <input
                        type="text"
                        value={customInputs[currentQuestion.id] || ''}
                        onChange={(e) => handleCustomInput(e.target.value)}
                        placeholder="Enter your custom detail..."
                        autoFocus
                        className="w-full px-4 py-3 bg-gray-950 border-2 border-indigo-500 rounded-lg text-white placeholder-gray-500 focus:border-indigo-400 focus:outline-none"
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        💡 Tip: Be specific! E.g., "Vintage 1960s Polaroid style with warm tones"
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {currentQuestion.type === 'text' && (
              <textarea
                value={answers[currentQuestion.id] || ''}
                onChange={(e) => handleAnswer(e.target.value)}
                placeholder={currentQuestion.placeholder}
                rows={4}
                className="w-full px-4 py-3 bg-gray-900 border-2 border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none resize-none"
              />
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-700 flex items-center justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className="px-4 py-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            ← Back
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSkip}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Skip
            </button>

            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLastQuestion ? 'Generate Image' : 'Next →'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
