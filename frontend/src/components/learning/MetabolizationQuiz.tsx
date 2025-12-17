/**
 * Metabolization Quiz Component
 *
 * Presents comprehension questions to ensure active learning.
 * Innovation 4: Transforms passive consumption into active engagement.
 */

import { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, Brain, ChevronRight, ChevronLeft } from 'lucide-react';
import type { MetabolizationQuestion, AnswerEvaluationResponse } from '@/services/metabolizationService';

export interface MetabolizationQuizProps {
  /** Whether the quiz modal is visible */
  isOpen: boolean;

  /** Callback to close the quiz */
  onClose: () => void;

  /** Title of the content being metabolized */
  contentTitle: string;

  /** Type of content */
  contentType: 'note' | 'document' | 'youtube';

  /** Generated questions */
  questions: MetabolizationQuestion[];

  /** Loading state */
  isLoading?: boolean;

  /** Callback to submit an answer */
  onSubmitAnswer: (question: MetabolizationQuestion, answer: string) => Promise<AnswerEvaluationResponse>;

  /** Callback when quiz is completed */
  onComplete?: (score: number) => void;
}

interface QuestionState {
  answer: string;
  evaluation?: AnswerEvaluationResponse;
  isSubmitted: boolean;
}

export function MetabolizationQuiz({
  isOpen,
  onClose,
  contentTitle,
  questions,
  isLoading = false,
  onSubmitAnswer,
  onComplete,
}: MetabolizationQuizProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [questionStates, setQuestionStates] = useState<QuestionState[]>(
    questions.map(() => ({ answer: '', isSubmitted: false }))
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset state when questions change
  useEffect(() => {
    if (questions.length > 0) {
      setQuestionStates(questions.map(() => ({ answer: '', isSubmitted: false })));
      setCurrentQuestionIndex(0);
    }
  }, [questions]);

  if (!isOpen) return null;

  // Early return if no questions yet (loading state)
  if (questions.length === 0 || questionStates.length === 0) {
    return (
      <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-stone-800 rounded-lg shadow-2xl max-w-3xl w-full p-6">
          <div className="flex flex-col items-center justify-center py-12 space-y-3">
            <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-stone-600 dark:text-stone-400">
              Generating questions...
            </p>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentState = questionStates[currentQuestionIndex];

  // Safety check: if currentState is undefined, don't render
  if (!currentQuestion || !currentState) {
    return null;
  }

  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
  const answeredCount = questionStates.filter((s) => s?.isSubmitted).length;

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'text-green-600 bg-green-100 dark:bg-green-900/50 dark:text-green-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/50 dark:text-yellow-200';
      case 'hard':
        return 'text-red-600 bg-red-100 dark:bg-red-900/50 dark:text-red-200';
      default:
        return 'text-stone-600 bg-stone-100 dark:bg-stone-900/50 dark:text-stone-200';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'recall':
        return '🧠';
      case 'comprehension':
        return '💭';
      case 'application':
        return '🔧';
      case 'synthesis':
        return '🔗';
      default:
        return '❓';
    }
  };

  const handleAnswerChange = (value: string) => {
    const newStates = [...questionStates];
    newStates[currentQuestionIndex] = {
      ...newStates[currentQuestionIndex],
      answer: value,
    };
    setQuestionStates(newStates);
  };

  const handleSubmitAnswer = async () => {
    if (!currentState.answer.trim()) return;

    setIsSubmitting(true);
    try {
      const evaluation = await onSubmitAnswer(currentQuestion, currentState.answer);

      const newStates = [...questionStates];
      newStates[currentQuestionIndex] = {
        ...newStates[currentQuestionIndex],
        evaluation,
        isSubmitted: true,
      };
      setQuestionStates(newStates);
    } catch (error) {
      console.error('Failed to evaluate answer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleComplete = () => {
    const totalScore =
      questionStates.reduce((sum, state) => sum + (state.evaluation?.score || 0), 0) /
      questionStates.length;
    onComplete?.(totalScore);
    onClose();
  };

  const allQuestionsAnswered = questionStates.every((s) => s.isSubmitted);
  const averageScore = allQuestionsAnswered
    ? questionStates.reduce((sum, state) => sum + (state.evaluation?.score || 0), 0) /
      questionStates.length
    : 0;

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-stone-800 rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-stone-200 dark:border-stone-700">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Brain className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              <div>
                <h2 className="text-xl font-semibold text-stone-900 dark:text-white">
                  Metabolization Quiz
                </h2>
                <p className="text-sm text-stone-600 dark:text-stone-400 mt-1">
                  {contentTitle}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-stone-100 dark:hover:bg-stone-700 rounded-lg transition-colors"
              aria-label="Close quiz"
            >
              <X className="w-5 h-5 text-stone-500" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm text-stone-600 dark:text-stone-400">
              <span>
                Question {currentQuestionIndex + 1} of {questions.length}
              </span>
              <span>
                {answeredCount} answered
              </span>
            </div>
            <div className="w-full bg-stone-200 dark:bg-stone-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-stone-600 dark:text-stone-400">
                Generating questions...
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Question Header */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-2xl">{getTypeIcon(currentQuestion.question_type)}</span>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded ${getDifficultyColor(
                    currentQuestion.difficulty
                  )}`}
                >
                  {currentQuestion.difficulty.toUpperCase()}
                </span>
                <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200">
                  {currentQuestion.question_type.toUpperCase()}
                </span>
              </div>

              {/* Question */}
              <div>
                <h3 className="text-lg font-medium text-stone-900 dark:text-white mb-4">
                  {currentQuestion.question}
                </h3>
                {!currentState.isSubmitted && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      💡 Hint: {currentQuestion.expected_answer_hints}
                    </p>
                  </div>
                )}
              </div>

              {/* Answer Input */}
              <div>
                <textarea
                  value={currentState.answer}
                  onChange={(e) => handleAnswerChange(e.target.value)}
                  disabled={currentState.isSubmitted}
                  placeholder="Type your answer here..."
                  className="w-full min-h-[150px] p-4 border border-stone-300 dark:border-stone-600 rounded-lg focus:ring-2 focus:ring-purple-600 focus:border-transparent dark:bg-stone-700 dark:text-white disabled:bg-stone-100 dark:disabled:bg-stone-800 disabled:cursor-not-allowed"
                />
              </div>

              {/* Submit Button */}
              {!currentState.isSubmitted && (
                <button
                  onClick={handleSubmitAnswer}
                  disabled={!currentState.answer.trim() || isSubmitting}
                  className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 disabled:bg-stone-400 text-white rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Evaluating...' : 'Submit Answer'}
                </button>
              )}

              {/* Evaluation Results */}
              {currentState.evaluation && (
                <div className="space-y-4 border-t border-stone-200 dark:border-stone-700 pt-6">
                  {/* Score */}
                  <div className="flex items-center gap-3">
                    {currentState.evaluation.score >= 0.7 ? (
                      <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                    ) : (
                      <AlertCircle className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                    )}
                    <div>
                      <div className="text-2xl font-bold text-stone-900 dark:text-white">
                        {Math.round(currentState.evaluation.score * 100)}%
                      </div>
                      <div className="text-sm text-stone-600 dark:text-stone-400">
                        Comprehension Score
                      </div>
                    </div>
                  </div>

                  {/* Feedback */}
                  <div className="bg-stone-50 dark:bg-stone-900 rounded-lg p-4">
                    <h4 className="font-semibold text-stone-900 dark:text-white mb-2">
                      Feedback
                    </h4>
                    <p className="text-sm text-stone-700 dark:text-stone-300">
                      {currentState.evaluation.feedback}
                    </p>
                  </div>

                  {/* Concepts Demonstrated */}
                  {currentState.evaluation?.concepts_demonstrated && currentState.evaluation.concepts_demonstrated.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-stone-900 dark:text-white mb-2 text-sm">
                        Concepts You Demonstrated:
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {currentState.evaluation.concepts_demonstrated.map((concept, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 text-xs bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200 rounded"
                          >
                            ✓ {concept}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Suggestions */}
                  {currentState.evaluation?.suggestions && currentState.evaluation.suggestions.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-stone-900 dark:text-white mb-2 text-sm">
                        Suggestions for Improvement:
                      </h4>
                      <ul className="space-y-1">
                        {currentState.evaluation.suggestions.map((suggestion, i) => (
                          <li
                            key={i}
                            className="text-sm text-stone-600 dark:text-stone-400 flex items-start gap-2"
                          >
                            <span className="text-purple-600 dark:text-purple-400 mt-0.5">
                              →
                            </span>
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer with Navigation */}
        <div className="p-6 border-t border-stone-200 dark:border-stone-700 space-y-4">
          {/* Average Score (if all answered) */}
          {allQuestionsAnswered && (
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-stone-700 dark:text-stone-300">
                    Overall Metabolization Score
                  </div>
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {Math.round(averageScore * 100)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-stone-600 dark:text-stone-400">
                    {averageScore >= 0.8
                      ? '🟢 Metabolized!'
                      : averageScore >= 0.6
                      ? '🟡 In Progress'
                      : '🔴 Needs Review'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex items-center justify-between gap-4">
            <button
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0}
              className="flex items-center gap-2 px-4 py-2 text-stone-700 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>

            {currentQuestionIndex < questions.length - 1 ? (
              <button
                onClick={handleNext}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleComplete}
                disabled={!allQuestionsAnswered}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-stone-400 text-white rounded-lg transition-colors disabled:cursor-not-allowed"
              >
                Complete Quiz
                <CheckCircle className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MetabolizationQuiz;
