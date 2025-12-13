'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const error = searchParams.get('error');

  // Redirect if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
      </div>
    );
  }

  // Already authenticated, will redirect
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100">
        <div className="text-gray-500">Redirecting...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100 p-4">
      <div className="w-full max-w-md">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-brand-700 mb-2">OpenPoke</h1>
          <p className="text-gray-600">Your AI-powered productivity assistant</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-semibold text-gray-800 text-center mb-6">
            Welcome Back
          </h2>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">
                {error === 'auth_failed'
                  ? 'Authentication failed. Please try again.'
                  : error === 'invalid_state'
                  ? 'Invalid request. Please try again.'
                  : `Error: ${error}`}
              </p>
            </div>
          )}

          {/* Google Sign In Button */}
          <button
            onClick={login}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-white border-2 border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 group"
          >
            {/* Google Logo */}
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            <span className="text-gray-700 font-medium group-hover:text-gray-900">
              Continue with Google
            </span>
          </button>

          {/* Info Text */}
          <p className="mt-6 text-center text-sm text-gray-500">
            By signing in, you agree to our Terms of Service and Privacy Policy.
          </p>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="p-3">
            <div className="text-2xl mb-1">📧</div>
            <div className="text-xs text-gray-600">Email Integration</div>
          </div>
          <div className="p-3">
            <div className="text-2xl mb-1">📅</div>
            <div className="text-xs text-gray-600">Calendar Sync</div>
          </div>
          <div className="p-3">
            <div className="text-2xl mb-1">🤖</div>
            <div className="text-xs text-gray-600">AI Assistant</div>
          </div>
        </div>
      </div>
    </div>
  );
}
