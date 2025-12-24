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

  const currentQuestion = questions[currentStep];
  const isLastQuestion = currentStep === questions.length - 1;
  const progress = ((currentStep + 1) / questions.length) * 100;

  // Build live prompt preview
  const promptPreview = useMemo(() => {
    const parts = [basicPrompt];

    if (answers.style) parts.push(answers.style.toLowerCase());
    if (answers.setting) parts.push(`set in ${answers.setting.toLowerCase()}`);
    if (answers.time) parts.push(`during ${answers.time.toLowerCase()}`);
    if (answers.season) parts.push(`in ${answers.season.toLowerCase()}`);
    if (answers.mood) parts.push(`${answers.mood.toLowerCase()} atmosphere`);
    if (answers.action) parts.push(answers.action.toLowerCase());
    if (answers.lighting) parts.push(`with ${answers.lighting.toLowerCase()}`);
    if (answers.angle) parts.push(`${answers.angle.toLowerCase()} perspective`);
    if (answers.colors) parts.push(`${answers.colors.toLowerCase()} color palette`);
    if (answers.complexity) parts.push(answers.complexity.toLowerCase());
    if (answers.detail) parts.push(answers.detail.toLowerCase());
    if (answers.extras && answers.extras.trim()) parts.push(answers.extras);

    parts.push('professional', 'high quality', 'detailed');

    return parts.join(', ');
  }, [basicPrompt, answers]);

  const handleAnswer = (value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: value,
    }));
  };

  const handleNext = () => {
    if (isLastQuestion) {
      onComplete(answers);
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
    return answers[currentQuestion.id] !== undefined;
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
