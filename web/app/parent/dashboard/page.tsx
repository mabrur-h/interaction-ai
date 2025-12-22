'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';

interface Child {
  id: string;
  display_name: string | null;
  email: string;
  initial_balance: number;
  created_at: string;
}

interface PendingInvite {
  id: number;
  code: string;
  child_name: string;
  initial_balance: number;
  expires_at: string;
  created_at: string;
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

export default function ParentDashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const router = useRouter();

  const [children, setChildren] = useState<Child[]>([]);
  const [invites, setInvites] = useState<PendingInvite[]>([]);
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
    try {
      const [childrenData, invitesData] = await Promise.all([
        api.getChildren(),
        api.getPendingInvites(),
      ]);
      setChildren(childrenData?.children || []);
      setInvites(invitesData?.invites || []);
    } catch (err) {
      console.error('Failed to load data', err);
      setError('Failed to load family data');
      setChildren([]);
      setInvites([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && isAdult) {
      loadData();
    }
  }, [isAuthenticated, isAdult, loadData]);

  const handleCancelInvite = async (inviteId: number) => {
    if (!confirm('Cancel this invite code?')) return;

    try {
      await api.cancelInvite(inviteId);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel invite');
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  // Show loading while auth is loading or not yet authenticated
  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  // Redirect if child user - show loading while redirect happens
  if (!isAdult) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 p-4 sm:p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-brand-700">Wally Junior</h1>
            <p className="text-gray-600">Parent Dashboard</p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              Back to Chat
            </Link>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-red-600 hover:text-red-700 border border-red-200 rounded-lg hover:bg-red-50"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
            <button onClick={() => setError(null)} className="text-red-500 text-sm underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Loading */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">Loading...</p>
          </div>
        ) : (
          <>
            {/* Add Child Button */}
            <Link
              href="/parent/create-child"
              className="block mb-8 bg-brand-600 hover:bg-brand-700 text-white text-center py-4 px-6 rounded-xl font-medium shadow-lg transition-colors"
            >
              + Add a Child Account
            </Link>

            {/* Pending Invites */}
            {invites && invites.length > 0 && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-gray-700 mb-4">
                  Pending Invites
                </h2>
                <div className="space-y-3">
                  {invites.map((invite) => (
                    <div
                      key={invite.id}
                      className="bg-yellow-50 border border-yellow-200 rounded-xl p-4"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-800">{invite.child_name}</p>
                          <p className="text-sm text-gray-500">
                            Starting balance: {formatMoney(invite.initial_balance)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-mono text-lg font-bold text-brand-600">
                            {invite.code}
                          </p>
                          <p className="text-xs text-gray-500">
                            Expires {formatDate(invite.expires_at)}
                          </p>
                        </div>
                      </div>
                      <div className="mt-3 flex justify-end">
                        <button
                          onClick={() => handleCancelInvite(invite.id)}
                          className="text-sm text-red-500 hover:text-red-700"
                        >
                          Cancel Invite
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Children List */}
            <section>
              <h2 className="text-lg font-semibold text-gray-700 mb-4">
                My Children ({children?.length || 0})
              </h2>

              {!children || children.length === 0 ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                  <div className="text-5xl mb-4">👨‍👧‍👦</div>
                  <h3 className="text-lg font-medium text-gray-700 mb-2">
                    No children yet
                  </h3>
                  <p className="text-gray-500 mb-4">
                    Add a child to start their financial education journey with Wally!
                  </p>
                  <Link
                    href="/parent/create-child"
                    className="inline-block bg-brand-600 hover:bg-brand-700 text-white py-2 px-6 rounded-lg"
                  >
                    Add Child
                  </Link>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {children.map((child) => (
                    <Link
                      key={child.id}
                      href={`/parent/child/${child.id}`}
                      className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 bg-gradient-to-br from-violet-500 to-purple-700 rounded-full flex items-center justify-center text-2xl">
                          🦉
                        </div>
                        <div className="flex-1">
                          <h3 className="font-bold text-gray-800 text-lg">
                            {child.display_name || 'Child'}
                          </h3>
                          <p className="text-sm text-gray-500">
                            Joined {formatDate(child.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 pt-4 border-t border-gray-100">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Initial Balance</span>
                          <span className="font-medium text-gray-800">
                            {formatMoney(child.initial_balance)}
                          </span>
                        </div>
                      </div>
                      <p className="mt-3 text-sm text-brand-600">View details →</p>
                    </Link>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
