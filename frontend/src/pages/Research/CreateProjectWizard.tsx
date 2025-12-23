/**
 * Create Project Wizard - Multi-step form for creating research projects
 *
 * Steps:
 * 1. Basic Info (name, description, goal)
 * 2. Research Settings (max sources, depth, source types)
 * 3. Schedule Configuration (schedule type, cron expression)
 * 4. Review & Create
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateProject } from '@/hooks/useResearchProjects';
import type { ResearchProjectCreate } from '@/services/research-api';

type WizardStep = 'basic' | 'settings' | 'schedule' | 'review';

const CreateProjectWizard: React.FC = () => {
  const navigate = useNavigate();
  const createProject = useCreateProject();

  const [currentStep, setCurrentStep] = useState<WizardStep>('basic');
  const [formData, setFormData] = useState<ResearchProjectCreate>({
    name: '',
    description: '',
    goal: '',
    schedule_type: 'manual',
    auto_generate_tasks: true,
    max_tasks_per_run: 5,
    default_max_sources: 10,
    default_depth: 'thorough',
    default_source_types: ['web', 'academic', 'news'],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const steps: { id: WizardStep; label: string; number: number }[] = [
    { id: 'basic', label: 'Basic Info', number: 1 },
    { id: 'settings', label: 'Research Settings', number: 2 },
    { id: 'schedule', label: 'Schedule', number: 3 },
    { id: 'review', label: 'Review', number: 4 },
  ];

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);

  const validateStep = (step: WizardStep): boolean => {
    const newErrors: Record<string, string> = {};

    if (step === 'basic') {
      if (!formData.name.trim()) {
        newErrors.name = 'Project name is required';
      }
      if (!formData.goal.trim()) {
        newErrors.goal = 'Research goal is required';
      }
    }

    if (step === 'schedule') {
      if (formData.schedule_type === 'custom' && !formData.schedule_cron?.trim()) {
        newErrors.schedule_cron = 'Cron expression is required for custom schedules';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (!validateStep(currentStep)) return;

    const nextIndex = currentStepIndex + 1;
    if (nextIndex < steps.length) {
      setCurrentStep(steps[nextIndex].id);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(steps[prevIndex].id);
    }
  };

  const handleSubmit = async () => {
    if (!validateStep('review')) return;

    try {
      const project = await createProject.mutateAsync(formData);
      navigate(`/research/projects/${project.id}`);
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  const updateFormData = (updates: Partial<ResearchProjectCreate>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Create Research Project
            </h1>
            <button
              onClick={() => navigate('/research')}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            >
              Cancel
            </button>
          </div>

          {/* Progress Steps */}
          <div className="mt-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div className="flex items-center">
                    <div
                      className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                        currentStepIndex >= index
                          ? 'border-blue-600 bg-blue-600 text-white'
                          : 'border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400'
                      }`}
                    >
                      {step.number}
                    </div>
                    <span
                      className={`ml-2 text-sm font-medium ${
                        currentStepIndex >= index
                          ? 'text-gray-900 dark:text-white'
                          : 'text-gray-500 dark:text-gray-400'
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`flex-1 h-0.5 mx-4 ${
                        currentStepIndex > index
                          ? 'bg-blue-600'
                          : 'bg-gray-300 dark:bg-gray-600'
                      }`}
                    />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Form Content */}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          {/* Step 1: Basic Info */}
          {currentStep === 'basic' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Project Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => updateFormData({ name: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.name
                      ? 'border-red-500'
                      : 'border-gray-300 dark:border-gray-600'
                  } dark:bg-gray-700 dark:text-white`}
                  placeholder="e.g., AI Safety Research"
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Description
                </label>
                <input
                  type="text"
                  value={formData.description || ''}
                  onChange={(e) => updateFormData({ description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Short description of your research project"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Research Goal *
                </label>
                <textarea
                  value={formData.goal}
                  onChange={(e) => updateFormData({ goal: e.target.value })}
                  rows={4}
                  className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.goal
                      ? 'border-red-500'
                      : 'border-gray-300 dark:border-gray-600'
                  } dark:bg-gray-700 dark:text-white`}
                  placeholder="What do you want to research? Be specific about your objectives..."
                />
                {errors.goal && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.goal}</p>
                )}
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Tip: A detailed goal helps generate better research tasks
                </p>
              </div>
            </div>
          )}

          {/* Step 2: Research Settings */}
          {currentStep === 'settings' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Research Depth
                </label>
                <select
                  value={formData.default_depth}
                  onChange={(e) =>
                    updateFormData({
                      default_depth: e.target.value as 'quick' | 'thorough' | 'deep',
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="quick">Quick (3-5 sources per task)</option>
                  <option value="thorough">Thorough (6-10 sources per task)</option>
                  <option value="deep">Deep (11-20 sources per task)</option>
                </select>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Deeper research takes longer but provides more comprehensive results
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Sources Per Task
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={formData.default_max_sources}
                  onChange={(e) =>
                    updateFormData({ default_max_sources: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Max Tasks Per Run
                </label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={formData.max_tasks_per_run}
                  onChange={(e) =>
                    updateFormData({ max_tasks_per_run: parseInt(e.target.value) })
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  How many tasks to execute each time the project runs
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Source Types
                </label>
                <div className="space-y-2">
                  {['web', 'academic', 'news', 'social'].map((type) => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.default_source_types?.includes(type) || false}
                        onChange={(e) => {
                          const current = formData.default_source_types || [];
                          if (e.target.checked) {
                            updateFormData({
                              default_source_types: [...current, type],
                            });
                          } else {
                            updateFormData({
                              default_source_types: current.filter((t) => t !== type),
                            });
                          }
                        }}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 capitalize">
                        {type}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.auto_generate_tasks}
                    onChange={(e) =>
                      updateFormData({ auto_generate_tasks: e.target.checked })
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                    Auto-generate research tasks using AI
                  </span>
                </label>
                <p className="mt-1 ml-6 text-sm text-gray-500 dark:text-gray-400">
                  Automatically creates research tasks based on your goal
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Schedule */}
          {currentStep === 'schedule' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Schedule Type
                </label>
                <select
                  value={formData.schedule_type}
                  onChange={(e) =>
                    updateFormData({
                      schedule_type: e.target.value as ResearchProjectCreate['schedule_type'],
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="manual">Manual (run when you want)</option>
                  <option value="daily">Daily (runs every day)</option>
                  <option value="weekly">Weekly (runs every week)</option>
                  <option value="monthly">Monthly (runs every month)</option>
                  <option value="custom">Custom (cron expression)</option>
                </select>
              </div>

              {formData.schedule_type === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Cron Expression *
                  </label>
                  <input
                    type="text"
                    value={formData.schedule_cron || ''}
                    onChange={(e) => updateFormData({ schedule_cron: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      errors.schedule_cron
                        ? 'border-red-500'
                        : 'border-gray-300 dark:border-gray-600'
                    } dark:bg-gray-700 dark:text-white`}
                    placeholder="0 2 * * *"
                  />
                  {errors.schedule_cron && (
                    <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                      {errors.schedule_cron}
                    </p>
                  )}
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Example: "0 2 * * *" runs at 2 AM every day
                  </p>
                </div>
              )}

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex">
                  <svg
                    className="h-5 w-5 text-blue-400"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                      Autonomous Research
                    </h3>
                    <div className="mt-2 text-sm text-blue-700 dark:text-blue-300">
                      <p>
                        Your research project will run automatically on schedule. You'll wake up
                        to new insights every day!
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 'review' && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Review Your Project
              </h3>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Project Name
                  </h4>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">{formData.name}</p>
                </div>

                {formData.description && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Description
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {formData.description}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Research Goal
                  </h4>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">{formData.goal}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Research Depth
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                      {formData.default_depth}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Max Sources
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {formData.default_max_sources}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Tasks Per Run
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {formData.max_tasks_per_run}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Schedule
                    </h4>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                      {formData.schedule_type}
                      {formData.schedule_type === 'custom' && formData.schedule_cron
                        ? ` (${formData.schedule_cron})`
                        : ''}
                    </p>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Features
                  </h4>
                  <ul className="mt-2 space-y-1">
                    {formData.auto_generate_tasks && (
                      <li className="text-sm text-gray-900 dark:text-white flex items-center">
                        <svg
                          className="h-4 w-4 text-green-500 mr-2"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                        Auto-generate research tasks with AI
                      </li>
                    )}
                    <li className="text-sm text-gray-900 dark:text-white flex items-center">
                      <svg
                        className="h-4 w-4 text-green-500 mr-2"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Source types: {formData.default_source_types?.join(', ')}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="mt-8 flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleBack}
              disabled={currentStepIndex === 0}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>

            <div className="flex gap-3">
              {currentStep !== 'review' && (
                <button
                  onClick={handleNext}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Next
                </button>
              )}

              {currentStep === 'review' && (
                <button
                  onClick={handleSubmit}
                  disabled={createProject.isPending}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                >
                  {createProject.isPending ? 'Creating...' : 'Create Project'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateProjectWizard;
