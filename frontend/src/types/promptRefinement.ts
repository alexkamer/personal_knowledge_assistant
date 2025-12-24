/**
 * TypeScript types for prompt refinement feature.
 */

export interface Question {
  id: string;
  question: string;
  type: 'single-select' | 'text';
  options?: string[];
  placeholder?: string;
}

export interface AnalyzePromptRequest {
  prompt: string;
}

export interface AnalyzePromptResponse {
  category: string;
  prompt: string;
  questions: Question[];
}

export interface BuildPromptRequest {
  basic_prompt: string;
  answers: Record<string, string>;
  category?: string;
}

export interface BuildPromptResponse {
  enhanced_prompt: string;
  negative_prompt: string;
  original_prompt: string;
}
