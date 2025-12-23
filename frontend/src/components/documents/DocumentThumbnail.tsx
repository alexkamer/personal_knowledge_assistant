/**
 * Document thumbnail component with fallback icons
 * Shows preview image or icon based on file type
 */
import { FileText, File, FileCode, Image as ImageIcon } from 'lucide-react';

interface DocumentThumbnailProps {
  fileType: string;
  filename: string;
  thumbnailUrl?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function DocumentThumbnail({
  fileType,
  filename,
  thumbnailUrl,
  size = 'md'
}: DocumentThumbnailProps) {
  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
  };

  const iconSizes = {
    sm: 24,
    md: 32,
    lg: 40,
  };

  const getFileTypeConfig = (type: string) => {
    const lowerType = type.toLowerCase();

    const configs: Record<string, { icon: any; gradient: string; iconColor: string }> = {
      pdf: {
        icon: FileText,
        gradient: 'from-red-500/20 to-red-600/20',
        iconColor: 'text-red-400',
      },
      doc: {
        icon: FileText,
        gradient: 'from-blue-500/20 to-blue-600/20',
        iconColor: 'text-blue-400',
      },
      docx: {
        icon: FileText,
        gradient: 'from-blue-500/20 to-blue-600/20',
        iconColor: 'text-blue-400',
      },
      txt: {
        icon: File,
        gradient: 'from-gray-500/20 to-gray-600/20',
        iconColor: 'text-gray-400',
      },
      md: {
        icon: FileCode,
        gradient: 'from-purple-500/20 to-purple-600/20',
        iconColor: 'text-purple-400',
      },
      jpg: {
        icon: ImageIcon,
        gradient: 'from-green-500/20 to-green-600/20',
        iconColor: 'text-green-400',
      },
      jpeg: {
        icon: ImageIcon,
        gradient: 'from-green-500/20 to-green-600/20',
        iconColor: 'text-green-400',
      },
      png: {
        icon: ImageIcon,
        gradient: 'from-green-500/20 to-green-600/20',
        iconColor: 'text-green-400',
      },
    };

    return configs[lowerType] || {
      icon: FileText,
      gradient: 'from-gray-500/20 to-gray-600/20',
      iconColor: 'text-gray-400',
    };
  };

  const config = getFileTypeConfig(fileType);
  const Icon = config.icon;

  return (
    <div className={`
      ${sizeClasses[size]}
      relative rounded-xl overflow-hidden
      glass elevated
      flex items-center justify-center
      bg-gradient-to-br ${config.gradient}
      group-hover:scale-105
      transition-transform duration-300
    `}>
      {thumbnailUrl ? (
        <>
          <img
            src={thumbnailUrl}
            alt={filename}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Hide image on error and show icon instead
              e.currentTarget.style.display = 'none';
            }}
          />
          {/* Fallback icon (hidden by default, shown on image error) */}
          <div className="absolute inset-0 flex items-center justify-center">
            <Icon className={config.iconColor} size={iconSizes[size]} />
          </div>
        </>
      ) : (
        <Icon className={config.iconColor} size={iconSizes[size]} />
      )}

      {/* File type badge */}
      <div className="
        absolute bottom-1 right-1
        px-1.5 py-0.5
        glass
        text-[10px] font-bold uppercase
        text-white
        rounded
      ">
        {fileType}
      </div>
    </div>
  );
}
