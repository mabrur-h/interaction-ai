'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { BottomNav, WallyAvatar, XPBar, StreakCounter, CoinBalance } from '@/components/wally';
import {
  mockUserStats,
  mockLessons,
  mockTasks,
  mockUserBadges,
  getLevelInfo,
  allBadges,
} from '@/lib/mockData';

export default function ProfilePage() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const router = useRouter();

  const isChild = user?.user_type === 'child';

  // Redirect if not authenticated or not a child
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login/child');
    } else if (!authLoading && isAuthenticated && !isChild) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, isChild, router]);

  if (authLoading || !isAuthenticated || !isChild) {
    return (
      <div className="min-h-screen flex items-center justify-center wally-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-neo-primary border-t-transparent" />
      </div>
    );
  }

  const stats = mockUserStats;
  const levelInfo = getLevelInfo(stats.xp);

  const completedLessons = mockLessons.filter((l) => l.progress === 100).length;
  const completedTasks = mockTasks.filter((t) => t.status === 'completed').length;
  const earnedBadges = mockUserBadges.length;

  const handleLogout = () => {
    logout();
    router.push('/login/child');
  };

  // Calculate days in streak
  const streakDays = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - i));
    const isActive = i >= 7 - stats.streak;
    return {
      day: date.toLocaleDateString('en-US', { weekday: 'short' }).charAt(0),
      isActive,
      isToday: i === 6,
    };
  });

  return (
    <div className="min-h-screen wally-bg pb-24">
      {/* Profile Header with gradient and glow */}
      <div
        className="relative px-4 pt-8 pb-20 overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(124, 58, 237, 0.2) 50%, rgba(0, 229, 204, 0.1) 100%)',
        }}
      >
        {/* Animated glow orbs */}
        <div className="absolute top-10 left-10 w-32 h-32 rounded-full bg-neo-accent/20 blur-3xl animate-pulse" />
        <div className="absolute top-20 right-10 w-24 h-24 rounded-full bg-neo-primary/20 blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />

        <div className="relative max-w-2xl mx-auto text-center text-white">
          {/* Avatar with glow ring */}
          <div className="relative inline-block mb-4">
            <div
              className="w-28 h-28 rounded-full flex items-center justify-center animate-pulse-glow"
              style={{
                background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(0, 229, 204, 0.2) 100%)',
                border: '2px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <WallyAvatar className="w-24 h-24 animate-float" />
            </div>
            <div
              className="absolute -bottom-1 -right-1 w-10 h-10 rounded-full flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #FACC15 0%, #FB923C 100%)',
                boxShadow: '0 0 20px rgba(250, 204, 21, 0.5)',
              }}
            >
              <span className="text-xl">⭐</span>
            </div>
          </div>

          {/* Name and level */}
          <h1 className="text-2xl font-bold mb-1 text-glow-cyan">
            {user?.display_name || 'Junior Saver'}
          </h1>
          <p className="text-white/60">
            Level {levelInfo.level} • <span className="text-neo-accent">{levelInfo.title}</span>
          </p>
        </div>
      </div>

      {/* Stats cards - overlapping header */}
      <div className="px-4 -mt-12 max-w-2xl mx-auto relative z-10">
        <div className="grid grid-cols-3 gap-3">
          <div className="card-neo p-4 text-center">
            <StreakCounter streak={stats.streak} className="justify-center mb-1" />
            <p className="text-xs text-white/50">Day Streak</p>
          </div>
          <div className="card-neo p-4 text-center">
            <div className="flex items-center justify-center gap-1 text-neo-accent mb-1">
              <span>⚡</span>
              <span className="font-bold text-lg text-glow-purple">{stats.xp}</span>
            </div>
            <p className="text-xs text-white/50">Total XP</p>
          </div>
          <div className="card-neo p-4 text-center">
            <CoinBalance coins={stats.coins} className="justify-center mb-1" />
            <p className="text-xs text-white/50">Coins</p>
          </div>
        </div>
      </div>

      <div className="px-4 py-6 max-w-2xl mx-auto relative z-10">
        {/* XP Progress to next level */}
        <div className="card-wally p-5 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-white">Level {levelInfo.level}</span>
            <span className="text-sm text-white/50">Level {levelInfo.level + 1}</span>
          </div>
          <XPBar xp={stats.xp} showLevel={false} />
          <p className="text-sm text-center text-white/50 mt-2">
            {levelInfo.maxXp - stats.xp} XP to next level
          </p>
        </div>

        {/* Streak calendar */}
        <div className="card-wally p-5 mb-6">
          <h2 className="font-bold text-white mb-4 flex items-center gap-2">
            <span>🔥</span> Your Streak
          </h2>
          <div className="flex justify-between">
            {streakDays.map((day, i) => (
              <div key={i} className="text-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-lg mb-1 transition-all ${
                    day.isToday ? 'ring-2 ring-neo-neon-orange ring-offset-2 ring-offset-neo-dark' : ''
                  }`}
                  style={{
                    background: day.isActive
                      ? 'linear-gradient(135deg, #FB923C 0%, #FF6B6B 100%)'
                      : 'rgba(255, 255, 255, 0.05)',
                    border: day.isActive ? 'none' : '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: day.isActive ? '0 0 15px rgba(251, 146, 60, 0.4)' : 'none',
                  }}
                >
                  {day.isActive ? '🔥' : ''}
                </div>
                <span className={`text-xs ${day.isToday ? 'font-bold text-neo-neon-orange' : 'text-white/40'}`}>
                  {day.day}
                </span>
              </div>
            ))}
          </div>
          <p className="text-sm text-center text-white/50 mt-4">
            {stats.streak} day streak! Keep it going!
          </p>
        </div>

        {/* Stats summary */}
        <div className="card-wally p-5 mb-6">
          <h2 className="font-bold text-white mb-4 flex items-center gap-2">
            <span>📊</span> Your Stats
          </h2>
          <div className="space-y-3">
            <Link
              href="/learn"
              className="flex items-center justify-between p-4 rounded-2xl transition-all hover:scale-[1.01]"
              style={{
                background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(124, 58, 237, 0.1) 100%)',
                border: '1px solid rgba(168, 85, 247, 0.2)',
              }}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">📚</span>
                <span className="font-medium text-white">Lessons Completed</span>
              </div>
              <span className="font-bold text-neo-accent">
                {completedLessons}/{mockLessons.length}
              </span>
            </Link>

            <Link
              href="/tasks"
              className="flex items-center justify-between p-4 rounded-2xl transition-all hover:scale-[1.01]"
              style={{
                background: 'linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(255, 107, 107, 0.1) 100%)',
                border: '1px solid rgba(251, 146, 60, 0.2)',
              }}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">✅</span>
                <span className="font-medium text-white">Tasks Completed</span>
              </div>
              <span className="font-bold text-neo-neon-orange">{completedTasks}</span>
            </Link>

            <Link
              href="/achievements"
              className="flex items-center justify-between p-4 rounded-2xl transition-all hover:scale-[1.01]"
              style={{
                background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.15) 0%, rgba(251, 146, 60, 0.1) 100%)',
                border: '1px solid rgba(250, 204, 21, 0.2)',
              }}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🏆</span>
                <span className="font-medium text-white">Badges Earned</span>
              </div>
              <span className="font-bold text-neo-neon-yellow">
                {earnedBadges}/{allBadges.length}
              </span>
            </Link>

            <Link
              href="/piggy-bank"
              className="flex items-center justify-between p-4 rounded-2xl transition-all hover:scale-[1.01]"
              style={{
                background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.15) 0%, rgba(74, 222, 128, 0.1) 100%)',
                border: '1px solid rgba(0, 229, 204, 0.2)',
              }}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">🐷</span>
                <span className="font-medium text-white">Savings Goals</span>
              </div>
              <span className="font-bold text-neo-primary">View</span>
            </Link>
          </div>
        </div>

        {/* Logout button */}
        <button
          onClick={handleLogout}
          className="w-full py-3 rounded-2xl font-medium transition-all btn-neo-ghost"
        >
          Bye! 👋 Log Out
        </button>
      </div>

      <BottomNav />
    </div>
  );
}
