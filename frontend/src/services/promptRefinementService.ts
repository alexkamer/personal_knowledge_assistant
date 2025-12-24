/**
 * Service for prompt refinement API calls.
 */
import type {
  AnalyzePromptRequest,
  AnalyzePromptResponse,
  BuildPromptRequest,
  BuildPromptResponse,
} from '@/types/promptRefinement';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const promptRefinementService = {
  /**
   * Analyze a prompt and get refinement questions.
   */
  async analyzePrompt(request: AnalyzePromptRequest): Promise<AnalyzePromptResponse> {
    const response = await fetch(`${API_BASE_URL}/prompts/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to analyze prompt: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Build an enhanced prompt from user answers.
   */
  async buildPrompt(request: BuildPromptRequest): Promise<BuildPromptResponse> {
    const response = await fetch(`${API_BASE_URL}/prompts/build`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to build prompt: ${response.statusText}`);
    }

    return response.json();
  },
};
