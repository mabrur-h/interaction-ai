'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api, setTokens } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

// Wally Owl SVG component
function WallyOwl({ className = '' }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Body */}
      <ellipse cx="50" cy="60" rx="35" ry="30" fill="#8B5CF6" />
      {/* Belly */}
      <ellipse cx="50" cy="65" rx="20" ry="18" fill="#DDD6FE" />
      {/* Head */}
      <circle cx="50" cy="35" r="28" fill="#8B5CF6" />
      {/* Face */}
      <ellipse cx="50" cy="40" rx="18" ry="15" fill="#DDD6FE" />
      {/* Left eye */}
      <circle cx="40" cy="35" r="10" fill="white" />
      <circle cx="42" cy="35" r="5" fill="#1F2937" />
      <circle cx="43" cy="33" r="2" fill="white" />
      {/* Right eye */}
      <circle cx="60" cy="35" r="10" fill="white" />
      <circle cx="62" cy="35" r="5" fill="#1F2937" />
      <circle cx="63" cy="33" r="2" fill="white" />
      {/* Beak */}
      <path d="M45 45 L50 55 L55 45 Z" fill="#F97316" />
      {/* Left ear tuft */}
      <path d="M25 20 Q30 5 35 15 Q30 12 28 20 Z" fill="#8B5CF6" />
      {/* Right ear tuft */}
      <path d="M75 20 Q70 5 65 15 Q70 12 72 20 Z" fill="#8B5CF6" />
      {/* Wings */}
      <ellipse cx="20" cy="55" rx="10" ry="20" fill="#7C3AED" />
      <ellipse cx="80" cy="55" rx="10" ry="20" fill="#7C3AED" />
      {/* Feet */}
      <ellipse cx="40" cy="88" rx="8" ry="5" fill="#F97316" />
      <ellipse cx="60" cy="88" rx="8" ry="5" fill="#F97316" />
    </svg>
  );
}

// Format amount in UZS (amount is already in so'm)
function formatMoney(amount: number): string {
  return new Intl.NumberFormat('uz-UZ').format(amount) + " so'm";
}

type Step = 'code' | 'password';

export default function ChildSignupPage() {
  const { isAuthenticated, isLoading: authLoading, refreshUser } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<Step>('code');
  const [inviteCode, setInviteCode] = useState('');
  const [childName, setChildName] = useState('');
  const [initialBalance, setInitialBalance] = useState(0);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, authLoading, router]);

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const result = await api.verifyInviteCode(inviteCode);
      setChildName(result.child_name);
      setInitialBalance(result.initial_balance);
      setStep('password');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid code');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setError("Passwords don't match!");
      return;
    }

    if (password.length < 4) {
      setError('Password must be at least 4 characters');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await api.childSignup(inviteCode, password);
      setTokens(result.access_token, result.refresh_token);
      await refreshUser();
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center wally-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-teal-500 border-t-transparent"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center wally-bg">
        <div className="text-gray-500 text-lg">Redirecting...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center wally-bg p-4">
      <div className="w-full max-w-md">
        {/* Wally Header */}
        <div className="text-center mb-6">
          <WallyOwl className="w-24 h-24 mx-auto mb-4 animate-bounce-in" />
          <h1 className="text-3xl font-bold text-violet-700 mb-1">
            Wally Junior
          </h1>
          <p className="text-gray-600 text-lg">
            {step === 'code' ? "Enter your invite code!" : `Hi ${childName}! Create a password.`}
          </p>
        </div>

        {/* Signup Card */}
        <div className="card-wally p-8">
          {step === 'code' ? (
            <>
              <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">
                Got an Invite Code?
              </h2>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-2xl">
                  <p className="text-red-700 text-center">{error}</p>
                </div>
              )}

              <form onSubmit={handleVerifyCode} className="space-y-5">
                <div>
                  <label htmlFor="code" className="block text-gray-700 font-medium mb-2">
                    Invite Code
                  </label>
                  <input
                    id="code"
                    type="text"
                    value={inviteCode}
                    onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
                    placeholder="Enter code from parent"
                    className="input-wally text-center text-2xl tracking-widest font-mono"
                    maxLength={8}
                    required
                    disabled={isLoading}
                  />
                  <p className="text-gray-500 text-sm text-center mt-2">
                    Ask your parent for the code!
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || inviteCode.length < 6}
                  className="w-full btn-wally text-lg py-4"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></span>
                      Checking...
                    </span>
                  ) : (
                    'Next'
                  )}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="text-center mb-6">
                <div className="inline-block bg-teal-100 rounded-2xl px-6 py-3 mb-4">
                  <p className="text-teal-800 font-bold text-xl">{childName}</p>
                  <p className="text-teal-600">
                    Starting with {formatMoney(initialBalance)}
                  </p>
                </div>
              </div>

              {error && (
                <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-2xl">
                  <p className="text-red-700 text-center">{error}</p>
                </div>
              )}

              <form onSubmit={handleSignup} className="space-y-5">
                <div>
                  <label htmlFor="password" className="block text-gray-700 font-medium mb-2">
                    Create a Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Your secret password"
                    className="input-wally"
                    minLength={4}
                    required
                    disabled={isLoading}
                  />
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-gray-700 font-medium mb-2">
                    Type it Again
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Same password again"
                    className="input-wally"
                    minLength={4}
                    required
                    disabled={isLoading}
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setStep('code');
                      setError(null);
                    }}
                    className="flex-1 px-6 py-3 rounded-full border-2 border-gray-300 text-gray-600 font-bold hover:bg-gray-50 transition-colors"
                    disabled={isLoading}
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 btn-wally text-lg py-3"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></span>
                        Creating...
                      </span>
                    ) : (
                      "Let's Go!"
                    )}
                  </button>
                </div>
              </form>
            </>
          )}

          {/* Links */}
          <div className="mt-6 text-center space-y-3">
            <p className="text-gray-600">
              Already have an account?{' '}
              <Link href="/login/child" className="text-teal-600 font-bold hover:underline">
                Log in
              </Link>
            </p>
            <p className="text-gray-500 text-sm">
              <Link href="/login" className="hover:underline">
                Parent login
              </Link>
            </p>
          </div>
        </div>

        {/* Fun icons */}
        <div className="mt-8 flex justify-center gap-6 text-3xl">
          <span title="Save money">🐷</span>
          <span title="Set goals">🎯</span>
          <span title="Have fun">🦉</span>
        </div>
      </div>
    </div>
  );
}
