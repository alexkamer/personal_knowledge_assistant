/**
 * Analytics dashboard showing document statistics
 */
import { HardDrive, FileText, Calendar, TrendingUp } from 'lucide-react';

interface DocumentsAnalyticsProps {
  totalDocuments: number;
  totalSize: number;
  recentUploads: number;
}

export function DocumentsAnalytics({ totalDocuments, totalSize, recentUploads }: DocumentsAnalyticsProps) {
  const formatSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const stats = [
    {
      label: 'Total Documents',
      value: totalDocuments,
      icon: FileText,
      color: 'text-primary-400',
      bgColor: 'bg-primary-500/10',
    },
    {
      label: 'Storage Used',
      value: formatSize(totalSize),
      icon: HardDrive,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Last 7 Days',
      value: recentUploads,
      icon: Calendar,
      color: 'text-success-400',
      bgColor: 'bg-success-500/10',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 fade-in">
      {stats.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.label}
            className={`glass glass-hover elevated p-6 rounded-xl fade-in stagger-${index + 1}`}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-1">{stat.label}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                <Icon className={stat.color} size={20} />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-1 text-xs text-success-400">
              <TrendingUp size={12} />
              <span>Active</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
