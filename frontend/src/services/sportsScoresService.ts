/**
 * Service for fetching sports scores from ESPN API
 */
import type { NBAScoreboardResponse } from '@/types/sportsScores';

const ESPN_API_BASE = 'https://site.api.espn.com/apis/site/v2/sports';

export type SportType = 'nba' | 'nhl';

/**
 * Fetch scores for a specific sport and date
 * @param sport - Sport type ('nba' or 'nhl')
 * @param date - Date in YYYYMMDD format (e.g., "20251223")
 * @returns Scoreboard data
 */
export async function fetchScores(sport: SportType, date: string): Promise<NBAScoreboardResponse> {
  const sportPath = sport === 'nba' ? 'basketball/nba' : 'hockey/nhl';
  const url = `${ESPN_API_BASE}/${sportPath}/scoreboard?limit=1000&dates=${date}`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch ${sport.toUpperCase()} scores: ${response.statusText}`);
  }

  const data = await response.json();
  return data as NBAScoreboardResponse;
}

/**
 * Fetch NBA scores for a specific date
 * @param date - Date in YYYYMMDD format (e.g., "20251223")
 * @returns NBA scoreboard data
 */
export async function fetchNBAScores(date: string): Promise<NBAScoreboardResponse> {
  return fetchScores('nba', date);
}

/**
 * Fetch NHL scores for a specific date
 * @param date - Date in YYYYMMDD format (e.g., "20251223")
 * @returns NHL scoreboard data
 */
export async function fetchNHLScores(date: string): Promise<NBAScoreboardResponse> {
  return fetchScores('nhl', date);
}

/**
 * Format a Date object to YYYYMMDD format for ESPN API
 * @param date - Date object
 * @returns Formatted date string
 */
export function formatDateForAPI(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
}

/**
 * Parse YYYYMMDD format to Date object
 * @param dateString - Date string in YYYYMMDD format
 * @returns Date object
 */
export function parseAPIDate(dateString: string): Date {
  const year = parseInt(dateString.substring(0, 4), 10);
  const month = parseInt(dateString.substring(4, 6), 10) - 1;
  const day = parseInt(dateString.substring(6, 8), 10);
  return new Date(year, month, day);
}

export const sportsScoresService = {
  fetchScores,
  fetchNBAScores,
  fetchNHLScores,
  formatDateForAPI,
  parseAPIDate,
};
