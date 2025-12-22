'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { KidHeader, BottomNav, WallyAvatar } from '@/components/wally';
import { api } from '@/lib/api';

// Types for API response
interface Achievement {
  type: string;
  name: string;
  description: string;
  emoji: string;
  earned: boolean;
  earned_at: string | null;
}

interface AchievementProgress {
  earned: number;
  total: number;
  progress_percent: number;
  remaining: number;
}

// Badge card component (inline since we need different structure)
function AchievementCard({
  achievement,
}: {
  achievement: Achievement;
}) {
  const isEarned = achievement.earned;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div
      className={`relative rounded-3xl p-4 transition-all duration-300 ${
        isEarned ? 'hover:scale-[1.03] cursor-pointer' : 'opacity-50'
      }`}
      style={{
        background: isEarned
          ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)'
          : 'rgba(255, 255, 255, 0.03)',
        border: `1px solid ${isEarned ? 'rgba(74, 222, 128, 0.4)' : 'rgba(255, 255, 255, 0.1)'}`,
        boxShadow: isEarned ? '0 0 25px rgba(74, 222, 128, 0.3)' : 'none',
      }}
    >
      {/* Badge icon */}
      <div className="text-center mb-3">
        <div
          className={`inline-flex w-16 h-16 rounded-full items-center justify-center text-3xl ${
            isEarned ? 'animate-float' : ''
          }`}
          style={{
            background: isEarned
              ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.4) 0%, rgba(74, 222, 128, 0.3) 100%)'
              : 'rgba(255, 255, 255, 0.05)',
            border: `2px solid ${isEarned ? 'rgba(255, 255, 255, 0.3)' : 'rgba(255, 255, 255, 0.1)'}`,
            boxShadow: isEarned ? '0 0 20px rgba(74, 222, 128, 0.3)' : 'none',
          }}
        >
          {isEarned ? achievement.emoji : '🔒'}
        </div>
      </div>

      {/* Badge info */}
      <div className="text-center">
        <h3 className={`font-bold ${isEarned ? 'text-white text-glow-cyan' : 'text-white/40'}`}>
          {achievement.name}
        </h3>
        <p className={`text-xs mt-1 ${isEarned ? 'text-white/60' : 'text-white/30'}`}>
          {achievement.description}
        </p>

        {/* Earned date */}
        {isEarned && achievement.earned_at && (
          <div className="mt-2">
            <span className="text-xs text-white/40">
              Earned {formatDate(achievement.earned_at)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AchievementsPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [progress, setProgress] = useState<AchievementProgress | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isChild = user?.user_type === 'child';

  const loadAchievements = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [allAchievements, progressData] = await Promise.all([
        api.getAllAchievements(),
        api.getAchievementProgress(),
      ]);
      setAchievements(allAchievements);
      setProgress(progressData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load achievements');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Redirect if not authenticated or not a child
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login/child');
    } else if (!authLoading && isAuthenticated && !isChild) {
      router.push('/');
    } else if (!authLoading && isAuthenticated && isChild) {
      loadAchievements();
    }
  }, [authLoading, isAuthenticated, isChild, router, loadAchievements]);

  if (authLoading || !isAuthenticated || !isChild || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center wally-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-neo-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen wally-bg pb-24">
        <KidHeader title="Achievements" />
        <div className="px-4 py-6 max-w-2xl mx-auto">
          <div className="card-wally p-5 text-center">
            <p className="text-red-400">{error}</p>
            <button
              onClick={loadAchievements}
              className="mt-4 px-4 py-2 bg-neo-primary text-white rounded-lg"
            >
              Retry
            </button>
          </div>
        </div>
        <BottomNav />
      </div>
    );
  }

  const earnedBadges = achievements.filter((a) => a.earned);
  const lockedBadges = achievements.filter((a) => !a.earned);

  return (
    <div className="min-h-screen wally-bg pb-24">
      <KidHeader title="Achievements" />

      <div className="px-4 py-6 max-w-2xl mx-auto">
        {/* Progress summary with glassmorphism */}
        <div className="card-wally p-5 mb-6">
          <div className="flex items-center gap-4">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #FACC15 0%, #FB923C 100%)',
                boxShadow: '0 0 30px rgba(250, 204, 21, 0.4)',
              }}
            >
              <span className="text-4xl">🏆</span>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white text-glow-cyan">
                {progress?.earned || 0} / {progress?.total || 0} Badges
              </h2>
              <p className="text-sm text-white/50">
                {progress?.remaining === 0
                  ? 'You collected them all!'
                  : `${progress?.remaining || 0} more to collect!`}
              </p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-4">
            <div
              className="h-3 rounded-full overflow-hidden"
              style={{
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${progress?.progress_percent || 0}%`,
                  background: 'linear-gradient(90deg, #FACC15 0%, #FB923C 100%)',
                  boxShadow: '0 0 15px rgba(250, 204, 21, 0.5)',
                }}
              />
            </div>
          </div>
        </div>

        {/* Earned badges */}
        {earnedBadges.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.3) 0%, rgba(251, 146, 60, 0.2) 100%)',
                  border: '1px solid rgba(250, 204, 21, 0.3)',
                }}
              >
                ⭐
              </span>
              <span className="text-glow-cyan">Your Badges</span>
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {earnedBadges.map((achievement) => (
                <AchievementCard key={achievement.type} achievement={achievement} />
              ))}
            </div>
          </section>
        )}

        {/* Locked badges */}
        {lockedBadges.length > 0 && (
          <section>
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span
                className="w-8 h-8 rounded-lg flex items-center justify-center"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                🔒
              </span>
              <span className="text-white/60">Badges to Unlock</span>
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {lockedBadges.map((achievement) => (
                <AchievementCard key={achievement.type} achievement={achievement} />
              ))}
            </div>
          </section>
        )}

        {/* Empty state */}
        {achievements.length === 0 && (
          <div
            className="text-center py-12 rounded-3xl"
            style={{
              background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.6) 0%, rgba(49, 46, 129, 0.4) 100%)',
              border: '1px solid rgba(0, 229, 204, 0.2)',
            }}
          >
            <div className="relative inline-block mb-4">
              <div
                className="w-20 h-20 rounded-full flex items-center justify-center animate-pulse-glow"
                style={{
                  background: 'linear-gradient(135deg, rgba(0, 229, 204, 0.2) 0%, rgba(168, 85, 247, 0.1) 100%)',
                  border: '2px solid rgba(0, 229, 204, 0.3)',
                }}
              >
                <WallyAvatar className="w-16 h-16 animate-float" />
              </div>
            </div>
            <h2 className="text-xl font-bold text-white mb-2 text-glow-cyan">
              No badges yet!
            </h2>
            <p className="text-white/50">
              Complete lessons and tasks to earn your first badge!
            </p>
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  );
}
