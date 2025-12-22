'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { KidHeader, BottomNav, WallyAvatar } from '@/components/wally';
import { TaskCard } from '@/components/tasks';
import { CelebrationModal } from '@/components/shared';
import { mockTasks } from '@/lib/mockData';
import type { Task } from '@/types/game';

export default function TasksPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [tasks, setTasks] = useState<Task[]>(mockTasks);
  const [showCelebration, setShowCelebration] = useState(false);
  const [celebrationReward, setCelebrationReward] = useState({ xp: 0, coins: 0 });
  const [activeTab, setActiveTab] = useState<'pending' | 'completed'>('pending');

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

  const handleCompleteTask = (taskId: string) => {
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;

    // Update task status
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId
          ? { ...t, status: 'completed' as const, completedAt: new Date().toISOString() }
          : t
      )
    );

    // Show celebration
    setCelebrationReward({ xp: task.xpReward || 0, coins: task.coinReward });
    setShowCelebration(true);
  };

  const pendingTasks = tasks.filter((t) => t.status === 'pending');
  const completedTasks = tasks.filter((t) => t.status === 'completed');

  return (
    <div className="min-h-screen wally-bg pb-24">
      <KidHeader title="My Tasks" />

      <div className="px-4 py-6 max-w-2xl mx-auto">
        {/* Summary card with glassmorphism */}
        <div className="card-wally p-5 mb-6">
          <div className="flex items-center gap-4">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, #FB923C 0%, #FF6B6B 100%)',
                boxShadow: '0 0 25px rgba(251, 146, 60, 0.4)',
              }}
            >
              <span className="text-3xl">✅</span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-white text-glow-cyan">
                {pendingTasks.length} tasks to do
              </h2>
              <p className="text-sm text-white/50">
                {completedTasks.length} completed this week
              </p>
            </div>
          </div>

          {/* Total rewards available */}
          {pendingTasks.length > 0 && (
            <div
              className="mt-4 pt-4"
              style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <p className="text-sm text-white/50 mb-3">Complete all to earn:</p>
              <div className="flex items-center gap-4">
                <div
                  className="flex items-center gap-2 px-4 py-2 rounded-xl"
                  style={{
                    background: 'linear-gradient(135deg, rgba(250, 204, 21, 0.2) 0%, rgba(251, 146, 60, 0.1) 100%)',
                    border: '1px solid rgba(250, 204, 21, 0.3)',
                  }}
                >
                  <span className="text-xl">🪙</span>
                  <span className="font-bold text-neo-neon-yellow">
                    {pendingTasks.reduce((sum, t) => sum + t.coinReward, 0)}
                  </span>
                </div>
                <div
                  className="flex items-center gap-2 px-4 py-2 rounded-xl"
                  style={{
                    background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(124, 58, 237, 0.1) 100%)',
                    border: '1px solid rgba(168, 85, 247, 0.3)',
                  }}
                >
                  <span className="text-lg">⚡</span>
                  <span className="font-bold text-neo-accent text-glow-purple">
                    +{pendingTasks.reduce((sum, t) => sum + (t.xpReward || 0), 0)} XP
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Neo-tech tabs */}
        <div
          className="flex gap-2 mb-6 p-1.5 rounded-2xl"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <button
            onClick={() => setActiveTab('pending')}
            className="flex-1 py-3 px-4 rounded-xl font-medium transition-all"
            style={{
              background: activeTab === 'pending'
                ? 'linear-gradient(135deg, rgba(0, 229, 204, 0.2) 0%, rgba(168, 85, 247, 0.1) 100%)'
                : 'transparent',
              border: activeTab === 'pending'
                ? '1px solid rgba(0, 229, 204, 0.3)'
                : '1px solid transparent',
              color: activeTab === 'pending' ? '#00E5CC' : 'rgba(255, 255, 255, 0.5)',
              boxShadow: activeTab === 'pending' ? '0 0 15px rgba(0, 229, 204, 0.2)' : 'none',
            }}
          >
            To Do ({pendingTasks.length})
          </button>
          <button
            onClick={() => setActiveTab('completed')}
            className="flex-1 py-3 px-4 rounded-xl font-medium transition-all"
            style={{
              background: activeTab === 'completed'
                ? 'linear-gradient(135deg, rgba(74, 222, 128, 0.2) 0%, rgba(0, 229, 204, 0.1) 100%)'
                : 'transparent',
              border: activeTab === 'completed'
                ? '1px solid rgba(74, 222, 128, 0.3)'
                : '1px solid transparent',
              color: activeTab === 'completed' ? '#4ADE80' : 'rgba(255, 255, 255, 0.5)',
              boxShadow: activeTab === 'completed' ? '0 0 15px rgba(74, 222, 128, 0.2)' : 'none',
            }}
          >
            Done ({completedTasks.length})
          </button>
        </div>

        {/* Task list */}
        {activeTab === 'pending' ? (
          pendingTasks.length > 0 ? (
            <div className="space-y-4">
              {pendingTasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onComplete={handleCompleteTask}
                />
              ))}
            </div>
          ) : (
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
                All done!
              </h2>
              <p className="text-white/50">
                No tasks right now. Ask your parents for more!
              </p>
            </div>
          )
        ) : completedTasks.length > 0 ? (
          <div className="space-y-4">
            {completedTasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        ) : (
          <div
            className="text-center py-12 rounded-3xl"
            style={{
              background: 'linear-gradient(135deg, rgba(30, 27, 75, 0.6) 0%, rgba(49, 46, 129, 0.4) 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <span className="text-5xl mb-4 block">📝</span>
            <h2 className="text-xl font-bold text-white mt-4 mb-2">
              No completed tasks yet
            </h2>
            <p className="text-white/50">
              Complete your first task to see it here!
            </p>
          </div>
        )}
      </div>

      <BottomNav />

      {/* Celebration modal */}
      <CelebrationModal
        isOpen={showCelebration}
        xpEarned={celebrationReward.xp}
        coinsEarned={celebrationReward.coins}
        message="Task Complete!"
        onClose={() => setShowCelebration(false)}
      />
    </div>
  );
}
