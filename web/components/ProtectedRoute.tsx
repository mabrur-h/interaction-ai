'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Protected route wrapper.
 * Redirects to login page if user is not authenticated.
 */
export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  // Show loading state
  if (isLoading) {
    return (
      fallback || (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
        </div>
      )
    );
  }

  // Not authenticated, will redirect
  if (!isAuthenticated) {
    return (
      fallback || (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-gray-500">Redirecting to login...</div>
        </div>
      )
    );
  }

  // Authenticated, render children
  return <>{children}</>;
}
