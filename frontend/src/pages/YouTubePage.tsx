/**
 * YouTube learning page for interactive video learning with transcripts.
 */
import { useState } from 'react';
import { Youtube, Search, FileText, Sparkles, AlertCircle, Loader2, CheckCircle } from 'lucide-react';
import { youtubeService, TranscriptData, VideoSummary } from '@/services/youtubeService';

export function YouTubePage() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transcriptData, setTranscriptData] = useState<TranscriptData | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [summary, setSummary] = useState<VideoSummary | null>(null);
  const [summarizing, setSummarizing] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const handleLoadVideo = async () => {
    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    setLoading(true);
    setError(null);
    setTranscriptData(null);
    setSummary(null);
    setSummaryError(null);

    try {
      const data = await youtubeService.getTranscript(url.trim());
      setTranscriptData(data);
      setCurrentTime(0);
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-red-500 rounded-lg">
              <Youtube className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                YouTube Learning
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
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
                className="w-full px-4 py-3 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                disabled={loading}
              />
              <Youtube className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            </div>
            <button
              onClick={handleLoadVideo}
              disabled={loading || !url.trim()}
              className="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
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
            <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Video Player Column */}
            <div className="lg:col-span-2 space-y-4">
              {/* Video Embed */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
                <div className="relative pb-[56.25%]">
                  <iframe
                    src={youtubeService.getEmbedUrl(transcriptData.video_id, currentTime)}
                    title="YouTube video player"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className="absolute inset-0 w-full h-full"
                  />
                </div>
              </div>

              {/* Video Info */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="font-semibold text-gray-900 dark:text-white">
                      Video Transcript
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {transcriptData.entry_count} entries •{' '}
                      {youtubeService.formatTimestamp(transcriptData.total_duration)} •{' '}
                      {transcriptData.language.toUpperCase()}
                      {transcriptData.is_generated && ' (Auto-generated)'}
                    </p>
                  </div>
                  <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                    <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </button>
                </div>
              </div>

              {/* AI Summary Section */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      AI Summary
                    </h3>
                  </div>
                  {!summary && !summarizing && (
                    <button
                      onClick={handleSummarize}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
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
                    <p className="text-sm text-gray-600 dark:text-gray-400">
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
                  <div className="space-y-4">
                    {/* Overall Summary */}
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                        Overview
                      </h4>
                      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                        {summary.summary}
                      </p>
                    </div>

                    {/* Key Points */}
                    {summary.key_points.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                          Key Points
                        </h4>
                        <ul className="space-y-2">
                          {summary.key_points.map((point, idx) => (
                            <li
                              key={idx}
                              className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300"
                            >
                              <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Topics */}
                    {summary.topics.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                          Topics Covered
                        </h4>
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

                    {/* Regenerate Button */}
                    <button
                      onClick={handleSummarize}
                      className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium transition-colors"
                    >
                      Regenerate Summary
                    </button>
                  </div>
                )}

                {/* Empty State */}
                {!summary && !summarizing && !summaryError && (
                  <div className="text-center py-8">
                    <Sparkles className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Click "Generate Summary" to get AI-powered insights
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Transcript Sidebar */}
            <div className="lg:col-span-1">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden sticky top-6">
                {/* Search */}
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="relative">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search transcript..."
                      className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-sm"
                    />
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  </div>
                </div>

                {/* Transcript Entries */}
                <div className="h-[600px] overflow-y-auto">
                  {transcriptData.transcript
                    .filter((entry) =>
                      searchQuery
                        ? entry.text.toLowerCase().includes(searchQuery.toLowerCase())
                        : true
                    )
                    .map((entry, index) => (
                      <button
                        key={index}
                        onClick={() => handleTimestampClick(entry.start)}
                        className="w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 border-b border-gray-100 dark:border-gray-700 transition-colors group"
                      >
                        <div className="flex items-start gap-3">
                          <span className="text-xs font-mono text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0 group-hover:underline">
                            {youtubeService.formatTimestamp(entry.start)}
                          </span>
                          <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                            {entry.text}
                          </span>
                        </div>
                      </button>
                    ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        // Empty State
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full mb-4">
              <Youtube className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Start Learning from YouTube
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
              Paste a YouTube URL above to get started. You'll see the transcript, AI
              summaries, and can ask questions about the video.
            </p>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
              <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400 mx-auto mb-2" />
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                  Interactive Transcript
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Click timestamps to jump to specific moments
                </p>
              </div>
              <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <Sparkles className="w-6 h-6 text-purple-600 dark:text-purple-400 mx-auto mb-2" />
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                  AI Summaries
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Get key takeaways and concepts
                </p>
              </div>
              <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <Search className="w-6 h-6 text-green-600 dark:text-green-400 mx-auto mb-2" />
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm mb-1">
                  Smart Search
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400">
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
