/**
 * Metadata badges component for displaying source chunk metadata.
 */
import { Code, List, Heading, FileText, Table, Layers } from 'lucide-react';

interface MetadataBadgesProps {
  contentType?: string;
  hasCode?: boolean;
  semanticDensity?: number;
}

export function MetadataBadges({ contentType, hasCode, semanticDensity }: MetadataBadgesProps) {
  const badges = [];

  // Content type badge
  if (contentType) {
    const contentTypeConfig = {
      paragraph: { icon: FileText, label: 'Paragraph', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' },
      list: { icon: List, label: 'List', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
      heading: { icon: Heading, label: 'Heading', color: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' },
      code: { icon: Code, label: 'Code', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
      table: { icon: Table, label: 'Table', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
    };

    const config = contentTypeConfig[contentType as keyof typeof contentTypeConfig];
    if (config) {
      const Icon = config.icon;
      badges.push(
        <span
          key="content-type"
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${config.color}`}
          title={`Content type: ${config.label}`}
        >
          <Icon size={12} />
          {config.label}
        </span>
      );
    }
  }

  // Code badge (if not already shown as content_type)
  if (hasCode && contentType !== 'code') {
    badges.push(
      <span
        key="has-code"
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
        title="Contains code"
      >
        <Code size={12} />
        Code
      </span>
    );
  }

  // Semantic density badge
  if (semanticDensity !== undefined && semanticDensity !== null) {
    const densityLabel = semanticDensity > 0.7 ? 'High' : semanticDensity > 0.4 ? 'Medium' : 'Low';
    const densityColor =
      semanticDensity > 0.7
        ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300'
        : semanticDensity > 0.4
        ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
        : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300';

    badges.push(
      <span
        key="density"
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${densityColor}`}
        title={`Semantic density: ${(semanticDensity * 100).toFixed(0)}% (information richness)`}
      >
        <Layers size={12} />
        {densityLabel} Density
      </span>
    );
  }

  if (badges.length === 0) {
    return null;
  }

  return <div className="flex flex-wrap gap-1.5">{badges}</div>;
}
