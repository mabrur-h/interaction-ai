'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';

interface ChildDetails {
  id: string;
  display_name: string | null;
  email: string;
  initial_balance: number;
  created_at: string;
  balance: number;
  total_spent: number;
  total_saved: number;
  recent_expenses: Array<{
    id: number;
    amount: number;
    category: string;
    description: string | null;
    expense_date: string;
  }>;
  savings_goals: Array<{
    id: number;
    name: string;
    target_amount: number;
    current_amount: number;
    emoji: string | null;
  }>;
}

// Format amount in UZS (amount is already in so'm)
function formatMoney(amount: number): string {
  return new Intl.NumberFormat('uz-UZ').format(amount) + " so'm";
}

// Format date
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('uz-UZ', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

// Category emoji
const categoryEmoji: Record<string, string> = {
  food: '🍕',
  toys: '🧸',
  games: '🎮',
  clothes: '👕',
  books: '📚',
  entertainment: '🎬',
  other: '📦',
};

export default function ChildDetailPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const childId = params.id as string;

  const [child, setChild] = useState<ChildDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAdult = user?.user_type !== 'child';

  // Redirect if not authenticated or is a child
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    } else if (!authLoading && isAuthenticated && !isAdult) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, isAdult, router]);

  const loadData = useCallback(async () => {
    if (!childId) return;

    try {
      const data = await api.getChildDetails(childId);
      setChild(data);
    } catch (err) {
      console.error('Failed to load child details', err);
      setError('Failed to load child details');
    } finally {
      setIsLoading(false);
    }
  }, [childId]);

  useEffect(() => {
    if (isAuthenticated && isAdult && childId) {
      loadData();
    }
  }, [isAuthenticated, isAdult, childId, loadData]);

  if (authLoading || !isAuthenticated || !isAdult) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !child) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 p-4 sm:p-6">
        <div className="max-w-md mx-auto text-center py-12">
          <div className="text-5xl mb-4">😕</div>
          <h2 className="text-xl font-bold text-gray-700 mb-2">
            {error || 'Child not found'}
          </h2>
          <Link
            href="/parent/dashboard"
            className="inline-block mt-4 text-brand-600 hover:underline"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 p-4 sm:p-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <header className="flex items-center gap-4 mb-6">
          <Link href="/parent/dashboard" className="text-gray-500 hover:text-gray-700">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-700 rounded-full flex items-center justify-center text-xl">
              🦉
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">
                {child.display_name || 'Child'}
              </h1>
              <p className="text-sm text-gray-500">
                Joined {formatDate(child.created_at)}
              </p>
            </div>
          </div>
        </header>

        {/* Stats Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <p className="text-xs text-gray-500 mb-1">Current Balance</p>
            <p className="text-lg font-bold text-teal-600">{formatMoney(child.balance)}</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <p className="text-xs text-gray-500 mb-1">Total Spent</p>
            <p className="text-lg font-bold text-orange-600">{formatMoney(child.total_spent)}</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <p className="text-xs text-gray-500 mb-1">Total Saved</p>
            <p className="text-lg font-bold text-green-600">{formatMoney(child.total_saved)}</p>
          </div>
        </div>

        {/* Savings Goals */}
        <section className="mb-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span>🐷</span> Savings Goals
          </h2>
          {child.savings_goals.length === 0 ? (
            <div className="bg-white rounded-xl p-4 text-center text-gray-500">
              No savings goals yet
            </div>
          ) : (
            <div className="space-y-3">
              {child.savings_goals.map((goal) => {
                const progress = goal.target_amount > 0
                  ? Math.round((goal.current_amount / goal.target_amount) * 100)
                  : 0;
                return (
                  <div key={goal.id} className="bg-white rounded-xl p-4 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{goal.emoji || '🎯'}</span>
                        <span className="font-medium text-gray-800">{goal.name}</span>
                      </div>
                      <span className="text-sm font-bold text-teal-600">{progress}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-green-400 to-teal-500 rounded-full"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      {formatMoney(goal.current_amount)} of {formatMoney(goal.target_amount)}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Recent Expenses */}
        <section>
          <h2 className="text-lg font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span>💸</span> Recent Expenses
          </h2>
          {child.recent_expenses.length === 0 ? (
            <div className="bg-white rounded-xl p-4 text-center text-gray-500">
              No expenses recorded yet
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm divide-y divide-gray-100">
              {child.recent_expenses.map((expense) => (
                <div key={expense.id} className="p-4 flex items-center gap-3">
                  <span className="text-2xl">
                    {categoryEmoji[expense.category] || '📦'}
                  </span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">
                      {expense.description || expense.category}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(expense.expense_date)}
                    </p>
                  </div>
                  <p className="font-medium text-orange-600">
                    -{formatMoney(expense.amount)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
