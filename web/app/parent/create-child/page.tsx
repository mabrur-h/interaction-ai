'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';

// Format amount in UZS (amount is already in so'm)
function formatMoney(amount: number): string {
  return new Intl.NumberFormat('uz-UZ').format(amount) + " so'm";
}

interface InviteResult {
  invite_code: string;
  child_name: string;
  initial_balance: number;
  expires_at: string;
}

export default function CreateChildPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [childName, setChildName] = useState('');
  const [initialBalance, setInitialBalance] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invite, setInvite] = useState<InviteResult | null>(null);

  const isAdult = user?.user_type !== 'child';

  // Redirect if not authenticated or is a child
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    } else if (!authLoading && isAuthenticated && !isAdult) {
      router.push('/');
    }
  }, [authLoading, isAuthenticated, isAdult, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const balance = parseFloat(initialBalance);
    if (!childName.trim() || balance < 0 || isNaN(balance)) {
      setError('Please enter a valid name and balance');
      setIsLoading(false);
      return;
    }

    try {
      // Send balance in so'm - backend will convert to cents
      const result = await api.createChildAccount(childName.trim(), balance);
      setInvite(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create invite');
    } finally {
      setIsLoading(false);
    }
  };

  const copyCode = () => {
    if (invite) {
      navigator.clipboard.writeText(invite.invite_code);
      alert('Code copied!');
    }
  };

  if (authLoading || !isAuthenticated || !isAdult) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 to-brand-100 p-4 sm:p-6">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <header className="flex items-center gap-4 mb-8">
          <Link href="/parent/dashboard" className="text-gray-500 hover:text-gray-700">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="text-xl font-bold text-brand-700">Add Child Account</h1>
        </header>

        {invite ? (
          /* Success - Show Invite Code */
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Invite Created!</h2>
            <p className="text-gray-600 mb-6">
              Share this code with <strong>{invite.child_name}</strong> to create their account.
            </p>

            <div className="bg-brand-50 rounded-xl p-6 mb-6">
              <p className="text-sm text-brand-600 mb-2">Invite Code</p>
              <p className="text-4xl font-mono font-bold text-brand-700 tracking-wider">
                {invite.invite_code}
              </p>
              <button
                onClick={copyCode}
                className="mt-3 text-sm text-brand-600 hover:text-brand-800 underline"
              >
                Copy Code
              </button>
            </div>

            <div className="text-left bg-gray-50 rounded-xl p-4 mb-6">
              <p className="text-sm text-gray-600">
                <strong>Starting balance:</strong> {formatMoney(invite.initial_balance)}
              </p>
              <p className="text-sm text-gray-600">
                <strong>Expires:</strong> {new Date(invite.expires_at).toLocaleDateString()}
              </p>
            </div>

            <div className="bg-violet-50 rounded-xl p-4 mb-6 text-left">
              <p className="font-medium text-violet-800 mb-2">Next steps:</p>
              <ol className="text-sm text-violet-700 list-decimal list-inside space-y-1">
                <li>Share the code with your child</li>
                <li>They visit the app and tap &quot;Sign Up&quot;</li>
                <li>They enter the code and create a password</li>
                <li>They&apos;re ready to learn with Wally!</li>
              </ol>
            </div>

            <div className="flex gap-3">
              <Link
                href="/parent/dashboard"
                className="flex-1 py-3 px-4 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium text-gray-700"
              >
                Back to Dashboard
              </Link>
              <button
                onClick={() => {
                  setInvite(null);
                  setChildName('');
                  setInitialBalance('');
                }}
                className="flex-1 py-3 px-4 bg-brand-600 hover:bg-brand-700 text-white rounded-lg font-medium"
              >
                Add Another
              </button>
            </div>
          </div>
        ) : (
          /* Form */
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-6">
              <div className="text-5xl mb-3">👧👦</div>
              <h2 className="text-xl font-bold text-gray-800">Add Your Child</h2>
              <p className="text-gray-500 text-sm mt-1">
                Create an invite code for your child to join Wally Junior
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-gray-700 font-medium mb-2">
                  Child&apos;s Name
                </label>
                <input
                  type="text"
                  value={childName}
                  onChange={(e) => setChildName(e.target.value)}
                  placeholder="Enter your child's name"
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                  required
                  disabled={isLoading}
                />
              </div>

              <div>
                <label className="block text-gray-700 font-medium mb-2">
                  Starting Balance (so&apos;m)
                </label>
                <input
                  type="number"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(e.target.value)}
                  placeholder="100000"
                  className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
                  min="0"
                  required
                  disabled={isLoading}
                />
                <p className="text-sm text-gray-500 mt-1">
                  This is how much allowance your child starts with
                </p>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 bg-brand-600 hover:bg-brand-700 text-white rounded-lg font-medium disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></span>
                    Creating...
                  </span>
                ) : (
                  'Create Invite Code'
                )}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
