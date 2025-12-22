/**
 * Game Types for Wally Junior - Duolingo-inspired gamification
 */

// =============================================================================
// User Stats & Progress
// =============================================================================

export interface UserStats {
  xp: number;
  level: number;
  coins: number;
  streak: number;
  lastActiveDate: string; // ISO date string
}

export interface LevelInfo {
  level: number;
  minXp: number;
  maxXp: number;
  title: string;
}

// =============================================================================
// Lessons & Learning
// =============================================================================

export interface Lesson {
  id: string;
  title: string;
  description: string;
  emoji: string;
  order: number;
  locked: boolean;
  progress: number; // 0-100
  xpReward: number;
  activities: Activity[];
}

export type ActivityType = 'quiz' | 'sorting' | 'budget' | 'match' | 'story' | 'info';

export interface Activity {
  id: string;
  type: ActivityType;
  data: QuizData | SortingData | BudgetData | MatchData | StoryData | InfoData;
}

// Quiz Activity - Multiple choice questions
export interface QuizData {
  question: string;
  options: QuizOption[];
  correctId: string;
  explanation?: string;
}

export interface QuizOption {
  id: string;
  label: string;
  emoji?: string;
}

// Sorting Activity - Drag items into categories
export interface SortingData {
  instruction: string;
  categories: SortingCategory[];
  items: SortingItem[];
}

export interface SortingCategory {
  id: string;
  label: string;
  emoji?: string;
}

export interface SortingItem {
  id: string;
  label: string;
  emoji?: string;
  correctCategoryId: string;
}

// Budget Activity - Allocate money to categories
export interface BudgetData {
  instruction: string;
  totalAmount: number;
  categories: BudgetCategory[];
  suggestedSplit?: Record<string, number>; // Recommended percentages
}

export interface BudgetCategory {
  id: string;
  label: string;
  emoji: string;
  minPercent?: number;
  maxPercent?: number;
}

// Match Activity - Match pairs together
export interface MatchData {
  instruction: string;
  pairs: MatchPair[];
}

export interface MatchPair {
  id: string;
  left: { label: string; emoji?: string };
  right: { label: string; emoji?: string };
}

// Story Activity - Interactive decision scenarios
export interface StoryData {
  story: string;
  wallyMessage?: string;
  choices: StoryChoice[];
}

export interface StoryChoice {
  id: string;
  label: string;
  emoji?: string;
  isGood: boolean; // For feedback
  feedback: string;
  xpBonus?: number;
}

// Info Activity - Educational content card
export interface InfoData {
  title: string;
  content: string;
  emoji?: string;
  wallyTip?: string;
}

// =============================================================================
// Tasks from Parents
// =============================================================================

export type TaskType = 'chore' | 'learning' | 'saving' | 'custom';
export type TaskStatus = 'pending' | 'completed' | 'expired';

export interface Task {
  id: string;
  title: string;
  description?: string;
  emoji: string;
  type: TaskType;
  status: TaskStatus;
  coinReward: number;
  xpReward?: number;
  assignedBy: string; // Parent name
  dueDate?: string; // ISO date string
  completedAt?: string;
  createdAt: string;
}

// =============================================================================
// Achievements & Badges
// =============================================================================

export type BadgeCategory = 'saving' | 'learning' | 'tasks' | 'streak' | 'social';

export interface Badge {
  id: string;
  name: string;
  description: string;
  emoji: string;
  category: BadgeCategory;
  requirement: string;
  xpReward: number;
}

export interface UserBadge {
  badgeId: string;
  earnedAt: string;
}

// =============================================================================
// Navigation & UI
// =============================================================================

export interface NavItem {
  href: string;
  icon: string;
  label: string;
  isActive?: boolean;
}

// =============================================================================
// Activity Results & Progress
// =============================================================================

export interface ActivityResult {
  activityId: string;
  correct: boolean;
  xpEarned: number;
  coinsEarned?: number;
  timestamp: string;
}

export interface LessonProgress {
  lessonId: string;
  completedActivities: string[];
  currentActivityIndex: number;
  startedAt: string;
  completedAt?: string;
}
