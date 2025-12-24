/**
 * Types for ESPN NBA Scoreboard API
 */

export interface NBAScoreboardResponse {
  leagues: League[];
  events: GameEvent[];
}

export interface League {
  id: string;
  uid: string;
  name: string;
  abbreviation: string;
  slug: string;
  season: Season;
  calendarType: string;
  calendarIsWhitelist: boolean;
  calendarStartDate: string;
  calendarEndDate: string;
}

export interface Season {
  year: number;
  startDate: string;
  endDate: string;
  displayName: string;
  type: SeasonType;
}

export interface SeasonType {
  id: string;
  type: number;
  name: string;
  abbreviation: string;
}

export interface GameEvent {
  id: string;
  uid: string;
  date: string;
  name: string;
  shortName: string;
  season: Season;
  competitions: Competition[];
  status: GameStatus;
}

export interface Competition {
  id: string;
  uid: string;
  date: string;
  attendance: number;
  type: {
    id: string;
    abbreviation: string;
  };
  timeValid: boolean;
  neutralSite: boolean;
  conferenceCompetition: boolean;
  playByPlayAvailable: boolean;
  recent: boolean;
  venue: Venue;
  competitors: Competitor[];
  status: GameStatus;
  broadcasts: Broadcast[];
  headlines?: Headline[];
}

export interface Venue {
  id: string;
  fullName: string;
  address: {
    city: string;
    state: string;
  };
  indoor: boolean;
}

export interface Competitor {
  id: string;
  uid: string;
  type: string;
  order: number;
  homeAway: 'home' | 'away';
  winner: boolean;
  team: Team;
  score: string;
  linescores?: LineScore[];
  statistics?: Statistic[];
  records?: Record[];
  leaders?: Leader[];
}

export interface Team {
  id: string;
  uid: string;
  location: string;
  name: string;
  abbreviation: string;
  displayName: string;
  shortDisplayName: string;
  color: string;
  alternateColor: string;
  isActive: boolean;
  logo: string;
}

export interface LineScore {
  value: number;
}

export interface Statistic {
  name: string;
  abbreviation: string;
  displayValue: string;
}

export interface Record {
  name: string;
  abbreviation?: string;
  type: string;
  summary: string;
}

export interface Leader {
  name: string;
  displayName: string;
  shortDisplayName: string;
  abbreviation: string;
  leaders: LeaderPlayer[];
}

export interface LeaderPlayer {
  displayValue: string;
  value: number;
  athlete: {
    id: string;
    fullName: string;
    displayName: string;
    shortName: string;
    links: Array<{ rel: string[]; href: string }>;
    headshot: string;
    jersey: string;
    position: {
      abbreviation: string;
    };
    team: {
      id: string;
    };
    active: boolean;
  };
  team: {
    id: string;
  };
}

export interface GameStatus {
  clock: number;
  displayClock: string;
  period: number;
  type: {
    id: string;
    name: string;
    state: string;
    completed: boolean;
    description: string;
    detail: string;
    shortDetail: string;
  };
}

export interface Broadcast {
  market: string;
  names: string[];
}

export interface Headline {
  description: string;
  type: string;
  shortLinkText: string;
}
