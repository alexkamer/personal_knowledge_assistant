/**
 * Timeline view of tool activity showing reasoning steps.
 */
import { ToolCall, ToolResult } from '@/types/chat';
import ToolCallDisplay from './ToolCallDisplay';
import ToolResultDisplay from './ToolResultDisplay';

interface Activity {
  type: 'tool_call' | 'tool_result';
  data: ToolCall | ToolResult;
  timestamp: number;
}

interface ActivityTimelineProps {
  toolCalls: ToolCall[];
  toolResults: ToolResult[];
}

export default function ActivityTimeline({ toolCalls, toolResults }: ActivityTimelineProps) {
  // Combine tool calls and results into a chronological timeline
  const activities: Activity[] = [];

  // Interleave tool calls and results based on order
  // Assumption: toolCalls[i] is followed by toolResults[i]
  const maxLength = Math.max(toolCalls.length, toolResults.length);
  for (let i = 0; i < maxLength; i++) {
    if (i < toolCalls.length) {
      activities.push({
        type: 'tool_call',
        data: toolCalls[i],
        timestamp: Date.now() + i * 2,
      });
    }
    if (i < toolResults.length) {
      activities.push({
        type: 'tool_result',
        data: toolResults[i],
        timestamp: Date.now() + i * 2 + 1,
      });
    }
  }

  // Sort by timestamp
  activities.sort((a, b) => a.timestamp - b.timestamp);

  if (activities.length === 0) {
    return null;
  }

  return (
    <div className="activity-timeline mb-4">
      <div className="text-sm font-semibold text-stone-700 dark:text-stone-300 mb-3 flex items-center gap-2">
        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
        Reasoning Steps
      </div>

      <div className="border-l-2 border-blue-300 dark:border-blue-700 ml-3 pl-4 space-y-3">
        {activities.map((activity, idx) => (
          <div key={idx} className="relative">
            {/* Timeline dot */}
            <div className="absolute -left-6 top-2 w-4 h-4 bg-blue-500 dark:bg-blue-600 rounded-full border-2 border-white dark:border-stone-900" />

            {/* Activity content */}
            {activity.type === 'tool_call' ? (
              <ToolCallDisplay toolCall={activity.data as ToolCall} />
            ) : (
              <ToolResultDisplay toolResult={activity.data as ToolResult} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
