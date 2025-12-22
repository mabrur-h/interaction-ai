'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  ReactNode,
} from 'react';
import {
  api,
  getAccessToken,
  setTokens,
  clearTokens,
  isAuthenticated as checkIsAuthenticated,
} from '@/lib/api';

/**
 * User type from the API.
 */
export interface User {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  timezone: string;
  created_at: string;
  user_type?: 'adult' | 'child';
  initial_balance?: number;
}

/**
 * Auth context state.
 */
interface AuthContextState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextState | undefined>(undefined);

/**
 * Auth provider props.
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Auth provider component.
 * Wraps the app and provides authentication state.
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Fetch the current user from the API.
   */
  const refreshUser = useCallback(async () => {
    if (!checkIsAuthenticated()) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch {
      // Token might be invalid, clear it
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Initialize auth state on mount.
   */
  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  /**
   * Redirect to Google OAuth login.
   */
  const login = useCallback(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    window.location.href = `${apiUrl}/api/v1/auth/google/login`;
  }, []);

  /**
   * Logout the current user.
   */
  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const value: AuthContextState = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context.
 */
export function useAuth(): AuthContextState {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Handle OAuth callback tokens.
 * Call this from the callback page to process tokens from the URL.
 */
export function handleAuthCallback(): boolean {
  if (typeof window === 'undefined') return false;

  const params = new URLSearchParams(window.location.search);
  const accessToken = params.get('access_token');
  const refreshToken = params.get('refresh_token');

  if (accessToken && refreshToken) {
    setTokens(accessToken, refreshToken);
    // Clean up URL
    window.history.replaceState({}, '', '/');
    return true;
  }

  return false;
}
