/**
 * Sports Scores Display Component
 * Shows NBA or NHL game scores for a selected date
 */
import { useState, useEffect } from 'react';
import { Calendar, RefreshCw, AlertCircle } from 'lucide-react';
import { sportsScoresService, type SportType } from '@/services/sportsScoresService';
import type { NBAScoreboardResponse, GameEvent, Competitor } from '@/types/sportsScores';

export function NBAScoresDisplay() {
  const [selectedSport, setSelectedSport] = useState<SportType>('nba');
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    // Default to today
    const today = new Date();
    return sportsScoresService.formatDateForAPI(today);
  });
  const [scoreboardData, setScoreboardData] = useState<NBAScoreboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedGames, setExpandedGames] = useState<Set<string>>(new Set());

  // Fetch scores when date or sport changes
  useEffect(() => {
    fetchScores();
    // Reset expanded games when switching sports
    setExpandedGames(new Set());
  }, [selectedDate, selectedSport]);

  const fetchScores = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await sportsScoresService.fetchScores(selectedSport, selectedDate);
      setScoreboardData(data);
    } catch (err: any) {
      console.error(`Failed to fetch ${selectedSport.toUpperCase()} scores:`, err);
      setError(err.message || `Failed to fetch ${selectedSport.toUpperCase()} scores`);
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const dateValue = e.target.value; // YYYY-MM-DD format
    const formatted = dateValue.replace(/-/g, ''); // Convert to YYYYMMDD
    setSelectedDate(formatted);
  };

  const getDateInputValue = () => {
    // Convert YYYYMMDD to YYYY-MM-DD for input
    if (selectedDate.length === 8) {
      return `${selectedDate.substring(0, 4)}-${selectedDate.substring(4, 6)}-${selectedDate.substring(6, 8)}`;
    }
    return '';
  };

  const formatDisplayDate = () => {
    const date = sportsScoresService.parseAPIDate(selectedDate);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getHomeTeam = (game: GameEvent): Competitor | undefined => {
    return game.competitions[0]?.competitors.find((c) => c.homeAway === 'home');
  };

  const getAwayTeam = (game: GameEvent): Competitor | undefined => {
    return game.competitions[0]?.competitors.find((c) => c.homeAway === 'away');
  };

  const getGameStatus = (game: GameEvent): string => {
    const status = game.competitions[0]?.status;
    if (!status) return '';

    if (status.type.completed) {
      return 'Final';
    } else if (status.type.state === 'in') {
      return `${status.displayClock} - Q${status.period}`;
    } else {
      // Scheduled
      const gameDate = new Date(game.date);
      return gameDate.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
      });
    }
  };

  const isGameLive = (game: GameEvent): boolean => {
    return game.competitions[0]?.status.type.state === 'in';
  };

  const isGameFinal = (game: GameEvent): boolean => {
    return game.competitions[0]?.status.type.completed || false;
  };

  const toggleGameExpanded = (gameId: string) => {
    setExpandedGames((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(gameId)) {
        newSet.delete(gameId);
      } else {
        newSet.add(gameId);
      }
      return newSet;
    });
  };

  const isGameExpanded = (gameId: string): boolean => {
    return expandedGames.has(gameId);
  };

  const getSportLabel = () => {
    return selectedSport === 'nba' ? 'NBA' : 'NHL';
  };

  const getPeriodLabel = (index: number) => {
    if (selectedSport === 'nba') {
      return index < 4 ? `Q${index + 1}` : `OT${index - 3}`;
    } else {
      return index < 3 ? `P${index + 1}` : `OT${index - 2}`;
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-950">
      {/* Header with Sport Toggle and Date Picker */}
      <div className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-white">{getSportLabel()} Scores</h2>
              <p className="text-sm text-gray-400 mt-1">{formatDisplayDate()}</p>
            </div>

            <div className="flex items-center gap-3">
              {/* Sport Toggle */}
              <div className="flex bg-gray-800 rounded-lg p-1">
                <button
                  onClick={() => setSelectedSport('nba')}
                  className={`px-4 py-1.5 rounded text-sm font-semibold transition-colors ${
                    selectedSport === 'nba'
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  NBA
                </button>
                <button
                  onClick={() => setSelectedSport('nhl')}
                  className={`px-4 py-1.5 rounded text-sm font-semibold transition-colors ${
                    selectedSport === 'nhl'
                      ? 'bg-indigo-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  NHL
                </button>
              </div>
              {/* Date Picker */}
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                <input
                  type="date"
                  value={getDateInputValue()}
                  onChange={handleDateChange}
                  className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Refresh Button */}
              <button
                onClick={fetchScores}
                disabled={loading}
                className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Refresh scores"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Scores Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-6">
          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
              <div>
                <h3 className="text-sm font-semibold text-red-200">Error</h3>
                <p className="text-sm text-red-300 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* No Games */}
          {!loading && !error && scoreboardData && scoreboardData.events.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg">No games scheduled for this date</p>
            </div>
          )}

          {/* Games Grid */}
          {!loading && !error && scoreboardData && scoreboardData.events.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {scoreboardData.events.map((game) => {
                const homeTeam = getHomeTeam(game);
                const awayTeam = getAwayTeam(game);
                const isLive = isGameLive(game);
                const isFinal = isGameFinal(game);

                if (!homeTeam || !awayTeam) return null;

                return (
                  <div
                    key={game.id}
                    className={`bg-gray-900 border rounded-lg overflow-hidden transition-all ${
                      isLive
                        ? 'border-green-500/50 shadow-lg shadow-green-500/20'
                        : 'border-gray-800 hover:border-gray-700'
                    }`}
                  >
                    {/* Game Status Header */}
                    <div
                      className={`px-4 py-2 text-xs font-semibold text-center ${
                        isLive
                          ? 'bg-green-600 text-white'
                          : isFinal
                          ? 'bg-gray-800 text-gray-300'
                          : 'bg-gray-800 text-gray-400'
                      }`}
                    >
                      {isLive && (
                        <span className="inline-flex items-center gap-1">
                          <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                          LIVE
                        </span>
                      )}{' '}
                      {getGameStatus(game)}
                    </div>

                    {/* Teams */}
                    <div className="p-4 space-y-3">
                      {/* Away Team */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <img
                            src={awayTeam.team.logo}
                            alt={awayTeam.team.displayName}
                            className="w-8 h-8 object-contain"
                          />
                          <div>
                            <p
                              className={`font-semibold ${
                                awayTeam.winner ? 'text-white' : 'text-gray-400'
                              }`}
                            >
                              {awayTeam.team.abbreviation}
                            </p>
                            <p className="text-xs text-gray-500">
                              {awayTeam.records?.[0]?.summary || ''}
                            </p>
                          </div>
                        </div>
                        <p
                          className={`text-2xl font-bold ${
                            awayTeam.winner ? 'text-white' : 'text-gray-500'
                          }`}
                        >
                          {awayTeam.score}
                        </p>
                      </div>

                      {/* Home Team */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <img
                            src={homeTeam.team.logo}
                            alt={homeTeam.team.displayName}
                            className="w-8 h-8 object-contain"
                          />
                          <div>
                            <p
                              className={`font-semibold ${
                                homeTeam.winner ? 'text-white' : 'text-gray-400'
                              }`}
                            >
                              {homeTeam.team.abbreviation}
                            </p>
                            <p className="text-xs text-gray-500">
                              {homeTeam.records?.[0]?.summary || ''}
                            </p>
                          </div>
                        </div>
                        <p
                          className={`text-2xl font-bold ${
                            homeTeam.winner ? 'text-white' : 'text-gray-500'
                          }`}
                        >
                          {homeTeam.score}
                        </p>
                      </div>
                    </div>

                    {/* Venue and Expander */}
                    <div className="px-4 pb-3">
                      <p className="text-xs text-gray-500 text-center">
                        {game.competitions[0]?.venue.fullName}
                      </p>

                      {/* Expander button for final games */}
                      {isFinal && (
                        <div className="flex justify-end mt-2">
                          <button
                            onClick={() => toggleGameExpanded(game.id)}
                            className="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1"
                          >
                            <span>{isGameExpanded(game.id) ? 'Hide' : 'Show'} Leaders</span>
                            <svg
                              className={`w-4 h-4 transition-transform ${
                                isGameExpanded(game.id) ? 'rotate-180' : ''
                              }`}
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 9l-7 7-7-7"
                              />
                            </svg>
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Leaders Section (Expandable) */}
                    {isFinal && isGameExpanded(game.id) && (
                      <div className="border-t border-gray-800 bg-gray-950 px-4 py-3">
                        {/* Line Scores */}
                        {(awayTeam.linescores || homeTeam.linescores) && (
                          <div className="mb-4">
                            <h4 className="text-xs font-semibold text-gray-400 mb-2">
                              {selectedSport === 'nba' ? 'Quarter-by-Quarter' : 'Period-by-Period'}
                            </h4>
                            <div className="bg-gray-900 rounded border border-gray-800 overflow-hidden">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b border-gray-800">
                                    <th className="text-left px-2 py-1.5 text-gray-400 font-semibold">
                                      Team
                                    </th>
                                    {awayTeam.linescores?.map((_, index) => (
                                      <th
                                        key={index}
                                        className="text-center px-2 py-1.5 text-gray-400 font-semibold"
                                      >
                                        {getPeriodLabel(index)}
                                      </th>
                                    ))}
                                    <th className="text-center px-2 py-1.5 text-gray-400 font-semibold">
                                      Total
                                    </th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {/* Away Team Line */}
                                  <tr className="border-b border-gray-800">
                                    <td className="px-2 py-1.5 text-white font-semibold">
                                      {awayTeam.team.abbreviation}
                                    </td>
                                    {awayTeam.linescores?.map((score, index) => (
                                      <td key={index} className="text-center px-2 py-1.5 text-gray-300">
                                        {score.value}
                                      </td>
                                    ))}
                                    <td className="text-center px-2 py-1.5 text-white font-bold">
                                      {awayTeam.score}
                                    </td>
                                  </tr>
                                  {/* Home Team Line */}
                                  <tr>
                                    <td className="px-2 py-1.5 text-white font-semibold">
                                      {homeTeam.team.abbreviation}
                                    </td>
                                    {homeTeam.linescores?.map((score, index) => (
                                      <td key={index} className="text-center px-2 py-1.5 text-gray-300">
                                        {score.value}
                                      </td>
                                    ))}
                                    <td className="text-center px-2 py-1.5 text-white font-bold">
                                      {homeTeam.score}
                                    </td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        <h4 className="text-xs font-semibold text-gray-400 mb-3">Game Leaders</h4>

                        <div className="space-y-4">
                          {/* Away Team Leaders */}
                          {awayTeam.leaders && awayTeam.leaders.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-white mb-2">
                                {awayTeam.team.abbreviation}
                              </p>
                              <div className="space-y-2">
                                {awayTeam.leaders.slice(0, 3).map((leaderCategory) => {
                                  const leader = leaderCategory.leaders[0];
                                  if (!leader) return null;
                                  return (
                                    <div
                                      key={leaderCategory.name}
                                      className="flex items-center justify-between text-xs"
                                    >
                                      <div className="flex items-center gap-2 flex-1">
                                        <img
                                          src={leader.athlete.headshot}
                                          alt={leader.athlete.displayName}
                                          className="w-6 h-6 rounded-full object-cover"
                                          onError={(e) => {
                                            e.currentTarget.style.display = 'none';
                                          }}
                                        />
                                        <div className="flex-1 min-w-0">
                                          <p className="text-gray-300 truncate">
                                            {leader.athlete.shortName}
                                          </p>
                                          <p className="text-gray-500">
                                            {leaderCategory.abbreviation}
                                          </p>
                                        </div>
                                      </div>
                                      <p className="text-white font-semibold ml-2">
                                        {leader.displayValue}
                                      </p>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}

                          {/* Home Team Leaders */}
                          {homeTeam.leaders && homeTeam.leaders.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-white mb-2">
                                {homeTeam.team.abbreviation}
                              </p>
                              <div className="space-y-2">
                                {homeTeam.leaders.slice(0, 3).map((leaderCategory) => {
                                  const leader = leaderCategory.leaders[0];
                                  if (!leader) return null;
                                  return (
                                    <div
                                      key={leaderCategory.name}
                                      className="flex items-center justify-between text-xs"
                                    >
                                      <div className="flex items-center gap-2 flex-1">
                                        <img
                                          src={leader.athlete.headshot}
                                          alt={leader.athlete.displayName}
                                          className="w-6 h-6 rounded-full object-cover"
                                          onError={(e) => {
                                            e.currentTarget.style.display = 'none';
                                          }}
                                        />
                                        <div className="flex-1 min-w-0">
                                          <p className="text-gray-300 truncate">
                                            {leader.athlete.shortName}
                                          </p>
                                          <p className="text-gray-500">
                                            {leaderCategory.abbreviation}
                                          </p>
                                        </div>
                                      </div>
                                      <p className="text-white font-semibold ml-2">
                                        {leader.displayValue}
                                      </p>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
