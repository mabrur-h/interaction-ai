'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { handleAuthCallback, useAuth } from '@/contexts/AuthContext';

export default function AuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshUser } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const processCallback = async () => {
      // Check for error in URL
      const error = searchParams.get('error');
      if (error) {
        setStatus('error');
        setErrorMessage(
          error === 'auth_failed'
            ? 'Authentication failed. Please try again.'
            : error === 'invalid_state'
            ? 'Invalid request. Please try again.'
            : `Error: ${error}`
        );
        return;
      }

      // Try to handle the callback (extract tokens from URL)
      const success = handleAuthCallback();

      if (success) {
        setStatus('success');
        // Refresh user data
        await refreshUser();
        // Redirect to home page
        setTimeout(() => {
          router.push('/');
        }, 1000);
      } else {
        setStatus('error');
        setErrorMessage('No authentication tokens found in the response.');
      }
    };

    processCallback();
  }, [searchParams, router, refreshUser]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-brand-100 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
        {status === 'processing' && (
          <>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Completing sign in...
            </h2>
            <p className="text-gray-600">Please wait while we authenticate you.</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-6 h-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Welcome back!
            </h2>
            <p className="text-gray-600">Redirecting you to the app...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-6 h-6 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Authentication Failed
            </h2>
            <p className="text-gray-600 mb-6">{errorMessage}</p>
            <button
              onClick={() => router.push('/login')}
              className="px-6 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
            >
              Back to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
}
