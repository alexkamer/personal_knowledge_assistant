/**
 * YouTube learning page for interactive video learning with transcripts.
 */
import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Youtube, Search, FileText, Sparkles, AlertCircle, Loader2, CheckCircle, X, Copy, Check, User, Eye, ChevronDown, ChevronUp, Download } from 'lucide-react';
import { youtubeService, TranscriptData, VideoSummary, VideoMetadata } from '@/services/youtubeService';
import { ContextPanel } from '@/components/context/ContextPanel';

export function YouTubePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transcriptData, setTranscriptData] = useState<TranscriptData | null>(null);
  const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [summary, setSummary] = useState<VideoSummary | null>(null);
  const [summarizing, setSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [copiedTranscript, setCopiedTranscript] = useState(false);
  const [copiedSummary, setCopiedSummary] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    keyPoints: true,
    topics: true,
  });
  const [isContextPanelCollapsed, setIsContextPanelCollapsed] = useState(false);

  const transcriptRefs = useRef<{ [key: number]: HTMLButtonElement | null }>({});

  // Toggle section expansion
  const toggleSection = (section: 'overview' | 'keyPoints' | 'topics') => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Load video from URL params on mount
  useEffect(() => {
    const videoId = searchParams.get('v');
    if (videoId) {
      const videoUrl = `https://www.youtube.com/watch?v=${videoId}`;
      setUrl(videoUrl);
      loadVideoById(videoId);
    }
  }, []);

  // Helper to load video by ID
  const loadVideoById = async (videoId: string) => {
    setLoading(true);
    setError(null);
    setTranscriptData(null);
    setMetadata(null);
    setSummary(null);
    setSummaryError(null);

    try {
      // Fetch transcript
      const data = await youtubeService.getTranscript(videoId);
      setTranscriptData(data);
      setCurrentTime(0);

      // Fetch metadata
      try {
        const metadataData = await youtubeService.getVideoMetadata(data.video_id);
        setMetadata(metadataData);
      } catch (metaErr) {
        console.warn('Failed to fetch video metadata:', metaErr);
        // Non-fatal: continue even if metadata fails
      }
    } catch (err: any) {
      console.error('Failed to load transcript:', err);
      setError(
        err.response?.data?.detail ||
          'Failed to load video transcript. Make sure the video has captions available.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLoadVideo = async () => {
    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    // Extract video ID from URL
    const extractedId = youtubeService.extractVideoId ?
      await youtubeService.extractVideoId(url.trim()).then(res => res.video_id).catch(() => null) :
      null;

    if (!extractedId) {
      setError('Invalid YouTube URL');
      return;
    }

    // Update URL params
    setSearchParams({ v: extractedId });

    // Load video
    await loadVideoById(extractedId);
  };

  // Find current transcript entry based on currentTime
  const getCurrentTranscriptIndex = () => {
    if (!transcriptData) return -1;

    for (let i = 0; i < transcriptData.transcript.length; i++) {
      const entry = transcriptData.transcript[i];
      const nextEntry = transcriptData.transcript[i + 1];

      if (currentTime >= entry.start && (!nextEntry || currentTime < nextEntry.start)) {
        return i;
      }
    }
    return -1;
  };

  // Auto-scroll to active transcript entry
  useEffect(() => {
    const currentIndex = getCurrentTranscriptIndex();
    if (currentIndex >= 0 && transcriptRefs.current[currentIndex]) {
      transcriptRefs.current[currentIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [currentTime, transcriptData]);

  // Copy transcript to clipboard
  const handleCopyTranscript = async () => {
    if (!transcriptData) return;

    const text = transcriptData.transcript
      .map(entry => `[${youtubeService.formatTimestamp(entry.start)}] ${entry.text}`)
      .join('\n');

    await navigator.clipboard.writeText(text);
    setCopiedTranscript(true);
    setTimeout(() => setCopiedTranscript(false), 2000);
  };

  // Copy summary to clipboard
  const handleCopySummary = async () => {
    if (!summary) return;

    const text = `## Summary\n\n${summary.summary}\n\n## Key Points\n\n${summary.key_points.map(p => `- ${p}`).join('\n')}\n\n## Topics\n\n${summary.topics.map(t => `- ${t}`).join('\n')}`;

    await navigator.clipboard.writeText(text);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2000);
  };

  // Download summary as markdown
  const handleDownloadSummary = () => {
    if (!summary || !metadata) return;

    const markdownContent = `# ${metadata.title}

**Channel**: ${metadata.channel}
**Views**: ${youtubeService.formatViewCount(metadata.view_count)}
**Published**: ${youtubeService.formatUploadDate(metadata.upload_date)}
**Video URL**: https://www.youtube.com/watch?v=${metadata.video_id}

---

## Summary

${summary.summary}

## Key Points

${summary.key_points.map(p => `- ${p}`).join('\n')}

## Topics Covered

${summary.topics.map(t => `- ${t}`).join('\n')}

---

*Generated with Personal Knowledge Assistant*
`;

    // Create a blob and download
    const blob = new Blob([markdownContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${metadata.video_id}-summary.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Get filtered transcript entries
  const filteredTranscript = transcriptData?.transcript.filter((entry) =>
    searchQuery
      ? entry.text.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  ) || [];

  const currentTranscriptIndex = getCurrentTranscriptIndex();

  const handleSummarize = async () => {
    if (!transcriptData) return;

    setSummarizing(true);
    setSummaryError(null);

    try {
      const summaryData = await youtubeService.summarizeVideo(transcriptData.video_id);
      setSummary(summaryData);
    } catch (err: any) {
      console.error('Failed to generate summary:', err);
      setSummaryError(
        err.response?.data?.detail || 'Failed to generate summary. Please try again.'
      );
    } finally {
      setSummarizing(false);
    }
  };

  const handleTimestampClick = (timestamp: number) => {
    setCurrentTime(timestamp);
    // TODO: Seek video to this timestamp
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleLoadVideo();
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 dark:bg-stone-900">
      {/* Header */}
      <div className="bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border-b border-stone-200/50 dark:border-stone-700/50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10 py-7">
          <div className="flex items-center gap-4 mb-5">
            <div className="p-2.5 bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-md">
              <Youtube className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-stone-900 dark:text-white">
                YouTube Learning
              </h1>
              <p className="text-sm font-medium text-stone-600 dark:text-stone-400 mt-0.5">
                Learn better from videos with AI-powered transcripts and summaries
              </p>
            </div>
          </div>

          {/* URL Input */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Paste YouTube URL here (e.g., https://www.youtube.com/watch?v=...)"
                className="w-full px-4 py-3 pr-10 bg-white/90 dark:bg-stone-700/90 backdrop-blur-xl border border-stone-300/50 dark:border-stone-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent dark:text-white shadow-sm transition-all"
                disabled={loading}
              />
              <Youtube className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-stone-400" />
            </div>
            <button
              onClick={handleLoadVideo}
              disabled={loading || !url.trim()}
              className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-xl font-medium shadow-md hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <FileText className="w-5 h-5" />
                  Load Transcript
                </>
              )}
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  Error loading video
                </p>
                <p className="text-sm text-red-600 dark:text-red-300 mt-1">{error}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      {transcriptData ? (
        <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Video Player Column */}
            <div className="lg:col-span-2 space-y-4">
              {/* Video Embed */}
              <div className="bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg overflow-hidden">
                <div className="relative pb-[56.25%]">
                  <iframe
                    src={youtubeService.getEmbedUrl(transcriptData.video_id, currentTime)}
                    title="YouTube video player"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className="absolute inset-0 w-full h-full rounded-2xl"
                  />
                </div>
              </div>

              {/* Video Metadata */}
              {metadata && (
                <div className="bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg p-5">
                  <h1 className="text-xl font-bold text-stone-900 dark:text-white mb-3">
                    {metadata.title}
                  </h1>
                  <div className="flex flex-wrap items-center gap-4 text-sm text-stone-600 dark:text-stone-400">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      <span className="font-medium">{metadata.channel}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      <span>{youtubeService.formatViewCount(metadata.view_count)}</span>
                    </div>
                    {metadata.upload_date && (
                      <span>• {youtubeService.formatUploadDate(metadata.upload_date)}</span>
                    )}
                  </div>
                </div>
              )}

              {/* Video Info */}
              <div className="bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex-1">
                    <h2 className="font-semibold text-stone-900 dark:text-white">
                      Video Transcript
                    </h2>
                    <p className="text-sm text-stone-600 dark:text-stone-400 mt-1">
                      {transcriptData.entry_count} entries •{' '}
                      {youtubeService.formatTimestamp(transcriptData.total_duration)} •{' '}
                      {transcriptData.language.toUpperCase()}
                      {transcriptData.is_generated && ' (Auto-generated)'}
                    </p>
                  </div>
                  <button
                    onClick={handleCopyTranscript}
                    className="px-3 py-2 hover:bg-stone-100 dark:hover:bg-stone-700 rounded-xl transition-colors flex items-center gap-2 text-sm font-medium text-stone-700 dark:text-stone-300"
                    title="Copy transcript to clipboard"
                  >
                    {copiedTranscript ? (
                      <>
                        <Check className="w-4 h-4 text-green-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="w-4 h-4" />
                        Copy
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* AI Summary Section */}
              <div className="bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    <h3 className="text-lg font-semibold text-stone-900 dark:text-white">
                      AI Summary
                    </h3>
                  </div>
                  {!summary && !summarizing && (
                    <button
                      onClick={handleSummarize}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-xl text-sm font-medium shadow-md hover:shadow-lg transition-all flex items-center gap-2"
                    >
                      <Sparkles className="w-4 h-4" />
                      Generate Summary
                    </button>
                  )}
                </div>

                {/* Loading State */}
                {summarizing && (
                  <div className="text-center py-8">
                    <Loader2 className="w-8 h-8 text-purple-600 dark:text-purple-400 mx-auto mb-3 animate-spin" />
                    <p className="text-sm text-stone-600 dark:text-stone-400">
                      Analyzing video with AI...
                    </p>
                  </div>
                )}

                {/* Error State */}
                {summaryError && (
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-600 dark:text-red-300">{summaryError}</p>
                  </div>
                )}

                {/* Summary Display */}
                {summary && !summarizing && (
                  <div className="space-y-3">
                    {/* Overall Summary */}
                    <div className="border border-stone-200 dark:border-stone-700 rounded-lg overflow-hidden">
                      <button
                        onClick={() => toggleSection('overview')}
                        className="w-full flex items-center justify-between p-3 hover:bg-stone-50 dark:hover:bg-stone-700/50 transition-colors"
                      >
                        <h4 className="text-sm font-semibold text-stone-900 dark:text-white">
                          Overview
                        </h4>
                        {expandedSections.overview ? (
                          <ChevronUp className="w-4 h-4 text-stone-500" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-stone-500" />
                        )}
                      </button>
                      {expandedSections.overview && (
                        <div className="px-3 pb-3">
                          <p className="text-sm text-stone-700 dark:text-stone-300 leading-relaxed">
                            {summary.summary}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Key Points */}
                    {summary.key_points.length > 0 && (
                      <div className="border border-stone-200 dark:border-stone-700 rounded-lg overflow-hidden">
                        <button
                          onClick={() => toggleSection('keyPoints')}
                          className="w-full flex items-center justify-between p-3 hover:bg-stone-50 dark:hover:bg-stone-700/50 transition-colors"
                        >
                          <h4 className="text-sm font-semibold text-stone-900 dark:text-white">
                            Key Points ({summary.key_points.length})
                          </h4>
                          {expandedSections.keyPoints ? (
                            <ChevronUp className="w-4 h-4 text-stone-500" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-stone-500" />
                          )}
                        </button>
                        {expandedSections.keyPoints && (
                          <div className="px-3 pb-3">
                            <ul className="space-y-2">
                              {summary.key_points.map((point, idx) => (
                                <li
                                  key={idx}
                                  className="flex items-start gap-2 text-sm text-stone-700 dark:text-stone-300"
                                >
                                  <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                                  <span>{point}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Topics */}
                    {summary.topics.length > 0 && (
                      <div className="border border-stone-200 dark:border-stone-700 rounded-lg overflow-hidden">
                        <button
                          onClick={() => toggleSection('topics')}
                          className="w-full flex items-center justify-between p-3 hover:bg-stone-50 dark:hover:bg-stone-700/50 transition-colors"
                        >
                          <h4 className="text-sm font-semibold text-stone-900 dark:text-white">
                            Topics Covered ({summary.topics.length})
                          </h4>
                          {expandedSections.topics ? (
                            <ChevronUp className="w-4 h-4 text-stone-500" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-stone-500" />
                          )}
                        </button>
                        {expandedSections.topics && (
                          <div className="px-3 pb-3">
                            <div className="flex flex-wrap gap-2">
                              {summary.topics.map((topic, idx) => (
                                <span
                                  key={idx}
                                  className="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded-full text-xs font-medium"
                                >
                                  {topic}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        onClick={handleCopySummary}
                        className="px-4 py-2 bg-stone-100 dark:bg-stone-700 hover:bg-stone-200 dark:hover:bg-stone-600 text-stone-700 dark:text-stone-300 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                      >
                        {copiedSummary ? (
                          <>
                            <Check className="w-4 h-4 text-green-600" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Copy
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleDownloadSummary}
                        className="px-4 py-2 bg-stone-100 dark:bg-stone-700 hover:bg-stone-200 dark:hover:bg-stone-600 text-stone-700 dark:text-stone-300 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                        title="Download as Markdown"
                      >
                        <Download className="w-4 h-4" />
                        Download
                      </button>
                      <button
                        onClick={handleSummarize}
                        className="px-4 py-2 bg-stone-100 dark:bg-stone-700 hover:bg-stone-200 dark:hover:bg-stone-600 text-stone-700 dark:text-stone-300 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                      >
                        Regenerate
                      </button>
                    </div>
                  </div>
                )}

                {/* Empty State */}
                {!summary && !summarizing && !summaryError && (
                  <div className="text-center py-8">
                    <Sparkles className="w-12 h-12 text-stone-400 dark:text-stone-600 mx-auto mb-3" />
                    <p className="text-sm text-stone-600 dark:text-stone-400">
                      Click "Generate Summary" to get AI-powered insights
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Transcript Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg overflow-hidden sticky top-6">
                {/* Search */}
                <div className="p-4 border-b border-stone-200/50 dark:border-stone-700/50">
                  <div className="relative">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search transcript..."
                      className="w-full px-4 py-2 pr-20 bg-white/90 dark:bg-stone-700/90 backdrop-blur-xl border border-stone-300/50 dark:border-stone-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent dark:text-white text-sm shadow-sm transition-all"
                    />
                    {searchQuery ? (
                      <button
                        onClick={() => setSearchQuery('')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-stone-200 dark:hover:bg-stone-600 rounded-lg transition-colors"
                        title="Clear search"
                      >
                        <X className="w-4 h-4 text-stone-500" />
                      </button>
                    ) : (
                      <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
                    )}
                  </div>
                  {searchQuery && (
                    <p className="text-xs text-stone-500 dark:text-stone-400 mt-2">
                      {filteredTranscript.length} {filteredTranscript.length === 1 ? 'result' : 'results'}
                    </p>
                  )}
                </div>

                {/* Transcript Entries */}
                <div className="h-[600px] overflow-y-auto">
                  {filteredTranscript.map((entry, index) => {
                    const originalIndex = transcriptData.transcript.indexOf(entry);
                    const isActive = originalIndex === currentTranscriptIndex;

                    return (
                      <button
                        key={index}
                        ref={(el) => {
                          if (el) transcriptRefs.current[originalIndex] = el;
                        }}
                        onClick={() => handleTimestampClick(entry.start)}
                        className={`w-full text-left px-4 py-3 hover:bg-stone-50 dark:hover:bg-stone-700 border-b border-stone-100 dark:border-stone-700 transition-all group ${
                          isActive
                            ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-600'
                            : ''
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <span
                            className={`text-xs font-mono mt-0.5 flex-shrink-0 group-hover:underline ${
                              isActive
                                ? 'text-blue-700 dark:text-blue-300 font-semibold'
                                : 'text-blue-600 dark:text-blue-400'
                            }`}
                          >
                            {youtubeService.formatTimestamp(entry.start)}
                          </span>
                          <span
                            className={`text-sm flex-1 ${
                              isActive
                                ? 'text-stone-900 dark:text-white font-medium'
                                : 'text-stone-700 dark:text-stone-300'
                            }`}
                          >
                            {searchQuery ? (
                              // Highlight search term
                              entry.text.split(new RegExp(`(${searchQuery})`, 'gi')).map((part, i) =>
                                part.toLowerCase() === searchQuery.toLowerCase() ? (
                                  <mark
                                    key={i}
                                    className="bg-yellow-200 dark:bg-yellow-700 text-stone-900 dark:text-white rounded px-0.5"
                                  >
                                    {part}
                                  </mark>
                                ) : (
                                  <span key={i}>{part}</span>
                                )
                              )
                            ) : (
                              entry.text
                            )}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Context Intelligence Panel */}
            <div className="lg:col-span-1">
              <ContextPanel
                sourceType="youtube"
                sourceId={transcriptData.video_id}
                isCollapsed={isContextPanelCollapsed}
                onToggle={() => setIsContextPanelCollapsed(!isContextPanelCollapsed)}
              />
            </div>
          </div>
        </div>
      ) : (
        // Empty State
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-red-500/20 to-red-600/20 dark:bg-red-900/20 rounded-2xl mb-4">
              <Youtube className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-stone-900 dark:text-white mb-2">
              Start Learning from YouTube
            </h2>
            <p className="text-stone-600 dark:text-stone-400 mb-6 max-w-md mx-auto">
              Paste a YouTube URL above to get started. You'll see the transcript, AI
              summaries, and can ask questions about the video.
            </p>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
              <div className="p-5 bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg">
                <FileText className="w-6 h-6 text-indigo-600 dark:text-indigo-400 mx-auto mb-2" />
                <h3 className="font-semibold text-stone-900 dark:text-white text-sm mb-1">
                  Interactive Transcript
                </h3>
                <p className="text-xs text-stone-600 dark:text-stone-400">
                  Click timestamps to jump to specific moments
                </p>
              </div>
              <div className="p-5 bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg">
                <Sparkles className="w-6 h-6 text-purple-600 dark:text-purple-400 mx-auto mb-2" />
                <h3 className="font-semibold text-stone-900 dark:text-white text-sm mb-1">
                  AI Summaries
                </h3>
                <p className="text-xs text-stone-600 dark:text-stone-400">
                  Get key takeaways and concepts
                </p>
              </div>
              <div className="p-5 bg-white/90 dark:bg-stone-800/90 backdrop-blur-xl border border-stone-200/50 dark:border-stone-700/50 rounded-2xl shadow-lg">
                <Search className="w-6 h-6 text-green-600 dark:text-green-400 mx-auto mb-2" />
                <h3 className="font-semibold text-stone-900 dark:text-white text-sm mb-1">
                  Smart Search
                </h3>
                <p className="text-xs text-stone-600 dark:text-stone-400">
                  Find specific moments instantly
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
