/**
 * Utility functions for exporting conversations as Markdown.
 */
import type { Message, SourceCitation, ConversationWithMessages } from '@/types/chat';

/**
 * Format a message as Markdown.
 */
function formatMessage(message: Message): string {
  const timestamp = new Date(message.created_at).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  let markdown = '';

  if (message.role === 'user') {
    markdown += `## 👤 User\n\n`;
    markdown += `*${timestamp}*\n\n`;
    markdown += `${message.content}\n\n`;
  } else {
    markdown += `## 🤖 Assistant\n\n`;
    markdown += `*${timestamp}${message.model_used ? ` • ${message.model_used}` : ''}*\n\n`;
    markdown += `${message.content}\n\n`;

    // Add sources if available
    if (message.sources && message.sources.length > 0) {
      markdown += `### 📚 Sources\n\n`;
      message.sources.forEach((source, index) => {
        const sourceIcon = source.source_type === 'note' ? '📝' :
                          source.source_type === 'web' ? '🌐' : '📄';
        markdown += `${index + 1}. ${sourceIcon} **${source.source_title}**`;
        if (source.section_title) {
          markdown += ` - ${source.section_title}`;
        }
        markdown += ` *(distance: ${source.distance.toFixed(3)})*\n`;
      });
      markdown += `\n`;
    }

    // Add suggested questions if available
    if (message.suggested_questions && message.suggested_questions.length > 0) {
      markdown += `### 💡 Suggested Follow-up Questions\n\n`;
      message.suggested_questions.forEach((question, index) => {
        markdown += `${index + 1}. ${question}\n`;
      });
      markdown += `\n`;
    }
  }

  markdown += `---\n\n`;
  return markdown;
}

/**
 * Export a conversation as Markdown.
 */
export function exportConversationAsMarkdown(conversation: ConversationWithMessages): string {
  let markdown = `# ${conversation.title}\n\n`;

  if (conversation.summary) {
    markdown += `> ${conversation.summary}\n\n`;
  }

  const createdDate = new Date(conversation.created_at).toLocaleString('en-US', {
    dateStyle: 'long',
    timeStyle: 'short',
  });

  markdown += `**Created:** ${createdDate}\n`;
  markdown += `**Messages:** ${conversation.messages.length}\n\n`;
  markdown += `---\n\n`;

  // Add each message
  conversation.messages.forEach(message => {
    markdown += formatMessage(message);
  });

  // Add footer
  markdown += `---\n\n`;
  markdown += `*Exported from Personal Knowledge Assistant on ${new Date().toLocaleString('en-US', {
    dateStyle: 'long',
    timeStyle: 'short',
  })}*\n`;

  return markdown;
}

/**
 * Download a conversation as a Markdown file.
 */
export function downloadConversationAsMarkdown(conversation: ConversationWithMessages): void {
  const markdown = exportConversationAsMarkdown(conversation);
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  // Create filename from title (sanitize for file system)
  const filename = `${conversation.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_${Date.now()}.md`;

  // Create download link and trigger click
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();

  // Cleanup
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy a conversation as Markdown to clipboard.
 */
export async function copyConversationAsMarkdown(conversation: ConversationWithMessages): Promise<void> {
  const markdown = exportConversationAsMarkdown(conversation);
  await navigator.clipboard.writeText(markdown);
}
