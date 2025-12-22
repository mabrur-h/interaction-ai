'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
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

export default function ChildLoginPage() {
  const { isAuthenticated, isLoading: authLoading, refreshUser } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const error = searchParams.get('error');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setLoginError(null);

    try {
      const result = await api.childLogin(email, password);
      setTokens(result.access_token, result.refresh_token);
      await refreshUser();
      router.push('/');
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : 'Login failed');
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
          <p className="text-gray-600 text-lg">Welcome back, friend!</p>
        </div>

        {/* Login Card */}
        <div className="card-wally p-8">
          <h2 className="text-2xl font-bold text-gray-800 text-center mb-6">
            Log In
          </h2>

          {/* Error Message */}
          {(error || loginError) && (
            <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-2xl">
              <p className="text-red-700 text-center">
                {loginError || (error === 'auth_failed' ? 'Oops! Check your email and password.' : `Error: ${error}`)}
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-gray-700 font-medium mb-2">
                Your Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your_name@wally.junior"
                className="input-wally"
                required
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-gray-700 font-medium mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your secret password"
                className="input-wally"
                required
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-wally text-lg py-4"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></span>
                  Logging in...
                </span>
              ) : (
                "Let's Go!"
              )}
            </button>
          </form>

          {/* Links */}
          <div className="mt-6 text-center space-y-3">
            <p className="text-gray-600">
              First time here?{' '}
              <Link href="/signup/child" className="text-teal-600 font-bold hover:underline">
                Sign up with invite code
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
          <span title="Learn about money">📚</span>
          <span title="Have fun">🎉</span>
        </div>
      </div>
    </div>
  );
}
