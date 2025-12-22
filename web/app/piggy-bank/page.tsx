'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { WallyAvatar } from '@/components/wally';

interface SavingsGoal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  status: string;
  emoji: string | null;
  created_at: string;
  completed_at: string | null;
}

// Format amount in UZS (amount is already in so'm)
function formatMoney(amount: number): string {
  return new Intl.NumberFormat('uz-UZ').format(amount);
}

// Calculate progress percentage
function getProgress(current: number, target: number): number {
  if (target === 0) return 0;
  return Math.min(100, Math.round((current / target) * 100));
}

// Default emojis for goals
const defaultEmojis = ['🎮', '🎁', '📱', '🎨', '⚽', '🎸', '📚', '🧸'];

export default function PiggyBankPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [balance, setBalance] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [showNewGoal, setShowNewGoal] = useState(false);
  const [newGoalName, setNewGoalName] = useState('');
  const [newGoalAmount, setNewGoalAmount] = useState('');
  const [newGoalEmoji, setNewGoalEmoji] = useState('🐷');
  const [error, setError] = useState<string | null>(null);
  const [addingToGoal, setAddingToGoal] = useState<number | null>(null);
  const [addAmount, setAddAmount] = useState('');

  const isChild = user?.user_type === 'child';

  // Redirect if not authenticated or not a child
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login/child');
    } else if (!authLoading && isAuthenticated && !isChild) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, isChild, router]);

  const loadData = useCallback(async () => {
    try {
      const [goalsData, balanceData] = await Promise.all([
        api.getSavingsGoals(),
        api.getBalance(),
      ]);
      setGoals(goalsData?.goals || []);
      setBalance(balanceData?.current_balance || 0);
    } catch (err) {
      console.error('Failed to load data', err);
      setError('Failed to load your goals');
      setGoals([]);
      setBalance(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && isChild) {
      loadData();
    }
  }, [isAuthenticated, isChild, loadData]);

  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const amount = parseFloat(newGoalAmount) * 100; // Convert to cents
    if (!newGoalName.trim() || amount <= 0) {
      setError('Please enter a name and amount');
      return;
    }

    try {
      await api.createSavingsGoal(newGoalName.trim(), amount, newGoalEmoji);
      setNewGoalName('');
      setNewGoalAmount('');
      setNewGoalEmoji('🐷');
      setShowNewGoal(false);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create goal');
    }
  };

  const handleAddToGoal = async (goalId: number) => {
    setError(null);
    const amount = parseFloat(addAmount) * 100;

    if (amount <= 0) {
      setError('Please enter an amount');
      return;
    }

    if (amount > balance) {
      setError("You don't have enough money!");
      return;
    }

    try {
      const result = await api.addToSavingsGoal(goalId, amount);
      setAddingToGoal(null);
      setAddAmount('');
      await loadData();

      if (result.completed) {
        // Show celebration!
        alert('🎉 Hoo-hoo! You reached your goal!');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add money');
    }
  };

  const handleDeleteGoal = async (goalId: number) => {
    if (!confirm('Are you sure you want to delete this goal?')) return;

    try {
      await api.deleteSavingsGoal(goalId);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete goal');
    }
  };

  if (authLoading || !isAuthenticated || !isChild) {
    return (
      <div className="min-h-screen flex items-center justify-center wally-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-teal-500 border-t-transparent"></div>
      </div>
    );
  }

  const activeGoals = goals.filter((g) => g.status === 'active');
  const completedGoals = goals.filter((g) => g.status === 'completed');

  return (
    <div className="min-h-screen wally-bg p-4 sm:p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <header className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-gray-500 hover:text-gray-700">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-2xl font-bold text-violet-700 flex items-center gap-2">
              <span className="text-3xl">🐷</span> My Piggy Bank
            </h1>
          </div>
          <div className="bg-teal-50 rounded-xl px-4 py-2">
            <p className="text-xs text-teal-600">Available</p>
            <p className="text-lg font-bold text-teal-700">{formatMoney(balance)}</p>
          </div>
        </header>

        {/* Error */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border-2 border-red-200 rounded-2xl">
            <p className="text-red-700">{error}</p>
            <button onClick={() => setError(null)} className="text-red-500 text-sm underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Loading */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-teal-500 border-t-transparent mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading your goals...</p>
          </div>
        ) : (
          <>
            {/* New Goal Form */}
            {showNewGoal ? (
              <div className="card-wally p-6 mb-6">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Create a New Goal</h2>
                <form onSubmit={handleCreateGoal} className="space-y-4">
                  <div>
                    <label className="block text-gray-700 font-medium mb-2">Pick an emoji</label>
                    <div className="flex gap-2 flex-wrap">
                      {defaultEmojis.map((emoji) => (
                        <button
                          key={emoji}
                          type="button"
                          onClick={() => setNewGoalEmoji(emoji)}
                          className={`text-3xl p-2 rounded-xl transition-all ${
                            newGoalEmoji === emoji
                              ? 'bg-teal-100 scale-110'
                              : 'hover:bg-gray-100'
                          }`}
                        >
                          {emoji}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-gray-700 font-medium mb-2">
                      What are you saving for?
                    </label>
                    <input
                      type="text"
                      value={newGoalName}
                      onChange={(e) => setNewGoalName(e.target.value)}
                      placeholder="New bike, video game..."
                      className="input-wally"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-gray-700 font-medium mb-2">
                      How much do you need? (so&apos;m)
                    </label>
                    <input
                      type="number"
                      value={newGoalAmount}
                      onChange={(e) => setNewGoalAmount(e.target.value)}
                      placeholder="100000"
                      className="input-wally"
                      min="1"
                      required
                    />
                  </div>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setShowNewGoal(false)}
                      className="flex-1 px-6 py-3 rounded-full border-2 border-gray-300 text-gray-600 font-bold hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button type="submit" className="flex-1 btn-wally">
                      Create Goal
                    </button>
                  </div>
                </form>
              </div>
            ) : (
              <button
                onClick={() => setShowNewGoal(true)}
                className="w-full btn-wally-secondary mb-6 py-4"
              >
                <span className="text-xl mr-2">+</span> New Savings Goal
              </button>
            )}

            {/* Active Goals */}
            {activeGoals.length > 0 ? (
              <div className="space-y-4 mb-8">
                <h2 className="text-lg font-bold text-gray-700">My Goals</h2>
                {activeGoals.map((goal) => {
                  const progress = getProgress(goal.current_amount, goal.target_amount);
                  return (
                    <div key={goal.id} className="card-wally p-5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-4xl">{goal.emoji || '🎯'}</span>
                          <div>
                            <h3 className="font-bold text-gray-800 text-lg">{goal.name}</h3>
                            <p className="text-gray-500 text-sm">
                              {formatMoney(goal.current_amount)} of {formatMoney(goal.target_amount)}
                            </p>
                          </div>
                        </div>
                        <span className="text-2xl font-bold text-teal-600">{progress}%</span>
                      </div>

                      {/* Progress bar */}
                      <div className="piggy-progress mb-4">
                        <div
                          className="piggy-progress-bar"
                          style={{ width: `${progress}%` }}
                        />
                      </div>

                      {/* Actions */}
                      {addingToGoal === goal.id ? (
                        <div className="flex gap-2">
                          <input
                            type="number"
                            value={addAmount}
                            onChange={(e) => setAddAmount(e.target.value)}
                            placeholder="Amount"
                            className="input-wally flex-1"
                            min="1"
                            autoFocus
                          />
                          <button
                            onClick={() => handleAddToGoal(goal.id)}
                            className="btn-wally px-4"
                          >
                            Add
                          </button>
                          <button
                            onClick={() => {
                              setAddingToGoal(null);
                              setAddAmount('');
                            }}
                            className="px-4 py-2 text-gray-500"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => setAddingToGoal(goal.id)}
                            className="btn-wally flex-1"
                          >
                            Add Money
                          </button>
                          <button
                            onClick={() => handleDeleteGoal(goal.id)}
                            className="px-4 py-2 text-red-400 hover:text-red-600"
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              !showNewGoal && (
                <div className="text-center py-8">
                  <WallyAvatar className="w-20 h-20 mx-auto mb-4" />
                  <h2 className="text-xl font-bold text-gray-700 mb-2">No goals yet!</h2>
                  <p className="text-gray-500 mb-4">
                    Start saving for something special!
                  </p>
                </div>
              )
            )}

            {/* Completed Goals */}
            {completedGoals.length > 0 && (
              <div className="space-y-4">
                <h2 className="text-lg font-bold text-gray-700 flex items-center gap-2">
                  <span>🏆</span> Completed Goals
                </h2>
                {completedGoals.map((goal) => (
                  <div key={goal.id} className="bg-green-50 rounded-2xl p-4 border-2 border-green-200">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{goal.emoji || '🎯'}</span>
                      <div>
                        <h3 className="font-bold text-green-800">{goal.name}</h3>
                        <p className="text-green-600 text-sm">
                          {formatMoney(goal.target_amount)} saved!
                        </p>
                      </div>
                      <span className="ml-auto text-2xl">✅</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
