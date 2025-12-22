'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { KidHeader, BottomNav, WallyAvatar } from '@/components/wally';
import { LessonMap } from '@/components/learn';
import { mockLessons, mockUserStats, getLevelInfo } from '@/lib/mockData';

export default function LearnPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
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

  const levelInfo = getLevelInfo(mockUserStats.xp);
  const completedLessons = mockLessons.filter((l) => l.progress === 100).length;
  const totalLessons = mockLessons.length;

  return (
    <div className="min-h-screen wally-bg pb-24">
      <KidHeader />

      <div className="px-4 py-6 max-w-2xl mx-auto">
        {/* Welcome section with glassmorphism */}
        <div className="card-wally p-5 mb-6">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center animate-pulse-glow"
                style={{
                  background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(0, 229, 204, 0.2) 100%)',
                  border: '2px solid rgba(0, 229, 204, 0.3)',
                }}
              >
                <WallyAvatar className="w-14 h-14 animate-float" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white text-glow-cyan">
                Hey, {user?.display_name || 'friend'}!
              </h1>
              <p className="text-white/60">
                You&apos;re a <span className="text-neo-accent font-medium text-glow-purple">{levelInfo.title}</span>!
              </p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-neo-primary">📚</span>
                <span className="text-sm text-neo-primary font-medium">
                  {completedLessons}/{totalLessons} lessons completed
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Continue learning prompt with neo gradient */}
        {completedLessons < totalLessons && (
          <div
            className="rounded-2xl p-4 mb-6 relative overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.2) 0%, rgba(168, 85, 247, 0.15) 100%)',
              border: '1px solid rgba(0, 229, 204, 0.3)',
              boxShadow: '0 0 30px rgba(0, 229, 204, 0.2)',
            }}
          >
            {/* Animated glow */}
            <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-neo-primary/20 blur-3xl animate-pulse" />

            <div className="flex items-center gap-3 relative z-10">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, #00E5CC 0%, #A855F7 100%)',
                  boxShadow: '0 0 20px rgba(0, 229, 204, 0.4)',
                }}
              >
                <span className="text-2xl">🎯</span>
              </div>
              <div>
                <p className="font-bold text-white text-glow-cyan">Keep going!</p>
                <p className="text-sm text-white/60">
                  Complete lessons to earn XP and unlock more!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* All complete celebration */}
        {completedLessons === totalLessons && (
          <div
            className="rounded-2xl p-5 mb-6 text-center relative overflow-hidden"
            style={{
              background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.2) 0%, rgba(251, 146, 60, 0.15) 100%)',
              border: '1px solid rgba(250, 204, 21, 0.3)',
              boxShadow: '0 0 30px rgba(250, 204, 21, 0.2)',
            }}
          >
            <div className="absolute top-0 left-0 w-24 h-24 rounded-full bg-neo-neon-yellow/20 blur-3xl animate-pulse" />
            <span className="text-5xl mb-2 block">🏆</span>
            <h2 className="text-xl font-bold text-white mb-1">Amazing!</h2>
            <p className="text-white/60">You&apos;ve completed all lessons!</p>
          </div>
        )}

        {/* Lesson Map */}
        <div className="py-4">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.3) 0%, rgba(124, 58, 237, 0.2) 100%)',
                border: '1px solid rgba(168, 85, 247, 0.3)',
              }}
            >
              🗺️
            </span>
            <span className="text-glow-purple">Your Learning Journey</span>
          </h2>
          <LessonMap lessons={mockLessons} />
        </div>
      </div>

      <BottomNav />
    </div>
  );
}
