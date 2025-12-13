'use client';

import { useAuth } from '@/contexts/AuthContext';

/**
 * Re-export useAuth hook for convenience.
 * This allows importing from @/hooks/useAuth instead of @/contexts/AuthContext.
 */
export { useAuth };

/**
 * Hook that requires authentication.
 * Throws an error if used when not authenticated.
 */
export function useRequiredAuth() {
  const auth = useAuth();

  if (!auth.isLoading && !auth.isAuthenticated) {
    throw new Error('Authentication required');
  }

  return auth;
}
