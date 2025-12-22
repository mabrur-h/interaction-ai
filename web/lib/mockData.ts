/**
 * Mock Data for Wally Junior Gamification
 * This will be replaced with API calls once backend is ready
 */

import type {
  UserStats,
  LevelInfo,
  Lesson,
  Task,
  Badge,
  UserBadge,
} from '@/types/game';

// =============================================================================
// User Stats
// =============================================================================

export const mockUserStats: UserStats = {
  xp: 1250,
  level: 5,
  coins: 2500,
  streak: 7,
  lastActiveDate: new Date().toISOString().split('T')[0],
};

// =============================================================================
// Level Definitions
// =============================================================================

export const levels: LevelInfo[] = [
  { level: 1, minXp: 0, maxXp: 100, title: 'Money Beginner' },
  { level: 2, minXp: 100, maxXp: 250, title: 'Coin Counter' },
  { level: 3, minXp: 250, maxXp: 500, title: 'Piggy Banker' },
  { level: 4, minXp: 500, maxXp: 850, title: 'Smart Saver' },
  { level: 5, minXp: 850, maxXp: 1300, title: 'Budget Buddy' },
  { level: 6, minXp: 1300, maxXp: 1850, title: 'Money Manager' },
  { level: 7, minXp: 1850, maxXp: 2500, title: 'Finance Friend' },
  { level: 8, minXp: 2500, maxXp: 3300, title: 'Savings Star' },
  { level: 9, minXp: 3300, maxXp: 4200, title: 'Money Master' },
  { level: 10, minXp: 4200, maxXp: 5500, title: 'Finance Champion' },
];

export function getLevelInfo(xp: number): LevelInfo {
  for (let i = levels.length - 1; i >= 0; i--) {
    if (xp >= levels[i].minXp) {
      return levels[i];
    }
  }
  return levels[0];
}

export function getXpProgress(xp: number): number {
  const level = getLevelInfo(xp);
  const xpInLevel = xp - level.minXp;
  const levelRange = level.maxXp - level.minXp;
  return Math.round((xpInLevel / levelRange) * 100);
}

// =============================================================================
// Lessons
// =============================================================================

export const mockLessons: Lesson[] = [
  {
    id: 'saving-basics',
    title: 'Saving Basics',
    description: 'Learn why saving money is important',
    emoji: '🐷',
    order: 1,
    locked: false,
    progress: 100,
    xpReward: 50,
    activities: [
      {
        id: 'sb-1',
        type: 'info',
        data: {
          title: 'What is Saving?',
          content: 'Saving means keeping some of your money instead of spending it all. It\'s like putting coins in a piggy bank!',
          emoji: '🐷',
          wallyTip: 'Even saving a little bit adds up over time!',
        },
      },
      {
        id: 'sb-2',
        type: 'quiz',
        data: {
          question: 'Why do we save money?',
          options: [
            { id: 'a', label: 'To buy things later', emoji: '🎯' },
            { id: 'b', label: 'To throw it away', emoji: '🗑️' },
            { id: 'c', label: 'To eat it', emoji: '🍽️' },
            { id: 'd', label: 'To hide it forever', emoji: '🙈' },
          ],
          correctId: 'a',
          explanation: 'We save money so we can buy things we want or need in the future!',
        },
      },
      {
        id: 'sb-3',
        type: 'quiz',
        data: {
          question: 'Where can you keep your savings?',
          options: [
            { id: 'a', label: 'Piggy Bank', emoji: '🐷' },
            { id: 'b', label: 'Under the bed', emoji: '🛏️' },
            { id: 'c', label: 'Bank Account', emoji: '🏦' },
            { id: 'd', label: 'All of these!', emoji: '✅' },
          ],
          correctId: 'd',
          explanation: 'You can save money in many places! A piggy bank, a bank account, or even a safe spot at home.',
        },
      },
    ],
  },
  {
    id: 'needs-vs-wants',
    title: 'Needs vs Wants',
    description: 'Learn the difference between needs and wants',
    emoji: '🤔',
    order: 2,
    locked: false,
    progress: 40,
    xpReward: 75,
    activities: [
      {
        id: 'nw-1',
        type: 'info',
        data: {
          title: 'Needs and Wants',
          content: 'Needs are things you must have to live, like food, water, and a home. Wants are things that are nice to have but you can live without, like toys and games.',
          emoji: '🤔',
          wallyTip: 'Always take care of needs first, then save for wants!',
        },
      },
      {
        id: 'nw-2',
        type: 'sorting',
        data: {
          instruction: 'Drag each item to the right category!',
          categories: [
            { id: 'needs', label: 'NEEDS', emoji: '✅' },
            { id: 'wants', label: 'WANTS', emoji: '🎁' },
          ],
          items: [
            { id: 'food', label: 'Food', emoji: '🍕', correctCategoryId: 'needs' },
            { id: 'games', label: 'Video Games', emoji: '🎮', correctCategoryId: 'wants' },
            { id: 'water', label: 'Water', emoji: '💧', correctCategoryId: 'needs' },
            { id: 'toys', label: 'Toys', emoji: '🧸', correctCategoryId: 'wants' },
            { id: 'clothes', label: 'Clothes', emoji: '👕', correctCategoryId: 'needs' },
            { id: 'candy', label: 'Candy', emoji: '🍬', correctCategoryId: 'wants' },
          ],
        },
      },
      {
        id: 'nw-3',
        type: 'quiz',
        data: {
          question: 'Which one is a NEED?',
          options: [
            { id: 'a', label: 'New phone', emoji: '📱' },
            { id: 'b', label: 'Medicine', emoji: '💊' },
            { id: 'c', label: 'Ice cream', emoji: '🍦' },
            { id: 'd', label: 'Movie ticket', emoji: '🎬' },
          ],
          correctId: 'b',
          explanation: 'Medicine is a need because it helps keep us healthy!',
        },
      },
    ],
  },
  {
    id: 'earning-money',
    title: 'Earning Money',
    description: 'Discover ways kids can earn money',
    emoji: '💪',
    order: 3,
    locked: true,
    progress: 0,
    xpReward: 75,
    activities: [
      {
        id: 'em-1',
        type: 'info',
        data: {
          title: 'Ways to Earn',
          content: 'Kids can earn money by doing chores, helping neighbors, or even selling things they make!',
          emoji: '💪',
          wallyTip: 'Ask your parents about chores you can do to earn allowance!',
        },
      },
      {
        id: 'em-2',
        type: 'quiz',
        data: {
          question: 'Which is a good way to earn money?',
          options: [
            { id: 'a', label: 'Help with dishes', emoji: '🍽️' },
            { id: 'b', label: 'Take a toy from a store', emoji: '🚫' },
            { id: 'c', label: 'Ask strangers', emoji: '❌' },
            { id: 'd', label: 'Do nothing', emoji: '😴' },
          ],
          correctId: 'a',
          explanation: 'Helping with chores is a great way to earn money at home!',
        },
      },
    ],
  },
  {
    id: 'smart-spending',
    title: 'Smart Spending',
    description: 'Learn how to spend wisely',
    emoji: '🛒',
    order: 4,
    locked: true,
    progress: 0,
    xpReward: 100,
    activities: [
      {
        id: 'ss-1',
        type: 'info',
        data: {
          title: 'Think Before You Buy',
          content: 'Before buying something, ask yourself: Do I really need this? Can I wait? Is there a better price somewhere else?',
          emoji: '🛒',
          wallyTip: 'Waiting a day before buying helps you make better choices!',
        },
      },
      {
        id: 'ss-2',
        type: 'story',
        data: {
          story: 'You\'re at the store with 10,000 so\'m. You see a toy you want for 8,000 so\'m and a snack for 3,000 so\'m. What do you do?',
          wallyMessage: 'Think carefully about your options!',
          choices: [
            {
              id: 'a',
              label: 'Buy both anyway',
              emoji: '🛒',
              isGood: false,
              feedback: 'Oops! You don\'t have enough money for both. Always check if you have enough!',
            },
            {
              id: 'b',
              label: 'Buy just the toy',
              emoji: '🧸',
              isGood: true,
              feedback: 'Smart choice! You got what you wanted and still have 2,000 so\'m left.',
              xpBonus: 10,
            },
            {
              id: 'c',
              label: 'Save for something bigger',
              emoji: '🐷',
              isGood: true,
              feedback: 'Great thinking! Saving up can help you buy something even better later!',
              xpBonus: 15,
            },
          ],
        },
      },
      {
        id: 'ss-3',
        type: 'budget',
        data: {
          instruction: 'You have 50,000 so\'m! How would you split it?',
          totalAmount: 50000,
          categories: [
            { id: 'save', label: 'Save', emoji: '🐷', minPercent: 10 },
            { id: 'spend', label: 'Spend', emoji: '🛒', maxPercent: 70 },
            { id: 'share', label: 'Share', emoji: '🎁', minPercent: 5 },
          ],
          suggestedSplit: { save: 50, spend: 40, share: 10 },
        },
      },
    ],
  },
  {
    id: 'goal-setting',
    title: 'Goal Setting',
    description: 'Set and achieve your money goals',
    emoji: '🎯',
    order: 5,
    locked: true,
    progress: 0,
    xpReward: 100,
    activities: [],
  },
  {
    id: 'sharing-giving',
    title: 'Sharing & Giving',
    description: 'Learn the joy of helping others',
    emoji: '💝',
    order: 6,
    locked: true,
    progress: 0,
    xpReward: 75,
    activities: [],
  },
];

// =============================================================================
// Tasks from Parents
// =============================================================================

export const mockTasks: Task[] = [
  {
    id: 'task-1',
    title: 'Clean your room',
    description: 'Make your bed, put away toys, and organize your desk',
    emoji: '🧹',
    type: 'chore',
    status: 'pending',
    coinReward: 500,
    xpReward: 25,
    assignedBy: 'Mom',
    dueDate: new Date().toISOString(),
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 'task-2',
    title: 'Help with dishes',
    description: 'Wash and dry the dinner dishes',
    emoji: '🍽️',
    type: 'chore',
    status: 'pending',
    coinReward: 300,
    xpReward: 15,
    assignedBy: 'Dad',
    dueDate: new Date().toISOString(),
    createdAt: new Date(Date.now() - 43200000).toISOString(),
  },
  {
    id: 'task-3',
    title: 'Read for 20 minutes',
    description: 'Read any book you like for at least 20 minutes',
    emoji: '📖',
    type: 'learning',
    status: 'pending',
    coinReward: 200,
    xpReward: 30,
    assignedBy: 'Mom',
    dueDate: new Date(Date.now() + 86400000).toISOString(),
    createdAt: new Date(Date.now() - 21600000).toISOString(),
  },
  {
    id: 'task-4',
    title: 'Complete a lesson',
    description: 'Finish any Wally lesson',
    emoji: '📚',
    type: 'learning',
    status: 'pending',
    coinReward: 100,
    xpReward: 20,
    assignedBy: 'Dad',
    createdAt: new Date(Date.now() - 10800000).toISOString(),
  },
  {
    id: 'task-5',
    title: 'Water the plants',
    description: 'Water all the plants in the living room',
    emoji: '🌱',
    type: 'chore',
    status: 'completed',
    coinReward: 150,
    xpReward: 10,
    assignedBy: 'Mom',
    completedAt: new Date(Date.now() - 86400000).toISOString(),
    createdAt: new Date(Date.now() - 172800000).toISOString(),
  },
];

// =============================================================================
// Badges & Achievements
// =============================================================================

export const allBadges: Badge[] = [
  {
    id: 'first-saver',
    name: 'First Saver',
    description: 'Create your first savings goal',
    emoji: '🌟',
    category: 'saving',
    requirement: 'Create 1 savings goal',
    xpReward: 50,
  },
  {
    id: 'on-fire',
    name: 'On Fire',
    description: 'Maintain a 7-day streak',
    emoji: '🔥',
    category: 'streak',
    requirement: '7-day streak',
    xpReward: 100,
  },
  {
    id: 'goal-getter',
    name: 'Goal Getter',
    description: 'Complete a savings goal',
    emoji: '🏆',
    category: 'saving',
    requirement: 'Complete 1 savings goal',
    xpReward: 150,
  },
  {
    id: 'learner',
    name: 'Quick Learner',
    description: 'Complete 5 lessons',
    emoji: '📚',
    category: 'learning',
    requirement: 'Complete 5 lessons',
    xpReward: 100,
  },
  {
    id: 'task-master',
    name: 'Task Master',
    description: 'Complete 10 tasks from parents',
    emoji: '💪',
    category: 'tasks',
    requirement: 'Complete 10 tasks',
    xpReward: 150,
  },
  {
    id: 'wallys-friend',
    name: "Wally's Friend",
    description: 'Chat with Wally 20 times',
    emoji: '🦉',
    category: 'social',
    requirement: 'Send 20 messages',
    xpReward: 75,
  },
  {
    id: 'money-wise',
    name: 'Money Wise',
    description: 'Track 10 expenses',
    emoji: '💰',
    category: 'saving',
    requirement: 'Log 10 expenses',
    xpReward: 75,
  },
  {
    id: 'super-saver',
    name: 'Super Saver',
    description: 'Save 100,000 so\'m total',
    emoji: '🦸',
    category: 'saving',
    requirement: 'Save 100,000 so\'m',
    xpReward: 200,
  },
  {
    id: 'streak-legend',
    name: 'Streak Legend',
    description: 'Maintain a 30-day streak',
    emoji: '⚡',
    category: 'streak',
    requirement: '30-day streak',
    xpReward: 300,
  },
  {
    id: 'helper',
    name: 'Super Helper',
    description: 'Complete 25 chore tasks',
    emoji: '🌈',
    category: 'tasks',
    requirement: 'Complete 25 chores',
    xpReward: 200,
  },
];

export const mockUserBadges: UserBadge[] = [
  { badgeId: 'first-saver', earnedAt: new Date(Date.now() - 604800000).toISOString() },
  { badgeId: 'on-fire', earnedAt: new Date(Date.now() - 86400000).toISOString() },
  { badgeId: 'learner', earnedAt: new Date(Date.now() - 259200000).toISOString() },
];

// =============================================================================
// Helper Functions
// =============================================================================

export function getEarnedBadges(): Badge[] {
  return allBadges.filter((badge) =>
    mockUserBadges.some((ub) => ub.badgeId === badge.id)
  );
}

export function getLockedBadges(): Badge[] {
  return allBadges.filter(
    (badge) => !mockUserBadges.some((ub) => ub.badgeId === badge.id)
  );
}

export function getPendingTasks(): Task[] {
  return mockTasks.filter((task) => task.status === 'pending');
}

export function getCompletedTasks(): Task[] {
  return mockTasks.filter((task) => task.status === 'completed');
}

export function getUnlockedLessons(): Lesson[] {
  return mockLessons.filter((lesson) => !lesson.locked);
}
