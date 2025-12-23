/**
 * SuggestedQuestionsSection Component
 *
 * Displays AI-generated questions for deeper exploration.
 */

import { HelpCircle, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export interface SuggestedQuestionsSectionProps {
  /** List of suggested questions */
  questions: string[];
}

/**
 * Suggested Questions Section - clickable questions that navigate to chat
 */
export function SuggestedQuestionsSection({
  questions,
}: SuggestedQuestionsSectionProps) {
  const navigate = useNavigate();

  const handleQuestionClick = (question: string) => {
    // Navigate to chat with pre-filled question
    navigate('/chat', { state: { prefillQuestion: question } });
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
        <HelpCircle className="w-4 h-4 text-purple-600 dark:text-purple-500" />
        Explore Further
      </h4>

      <div className="space-y-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => handleQuestionClick(question)}
            className="w-full text-left p-3 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 rounded-lg transition-colors border border-purple-200 dark:border-purple-800 group"
          >
            <div className="flex items-start gap-3">
              <MessageSquare className="w-4 h-4 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-gray-800 dark:text-gray-200 group-hover:text-purple-900 dark:group-hover:text-purple-100 transition-colors">
                {question}
              </p>
            </div>
          </button>
        ))}
      </div>

      <p className="text-xs text-gray-500 dark:text-gray-400 mt-3 italic">
        Click any question to explore it in chat
      </p>
    </div>
  );
}

export default SuggestedQuestionsSection;
