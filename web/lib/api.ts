/**
 * API client with authentication support.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// Token storage keys
const ACCESS_TOKEN_KEY = 'openpoke_access_token';
const REFRESH_TOKEN_KEY = 'openpoke_refresh_token';

/**
 * Get the stored access token.
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get the stored refresh token.
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Store tokens in localStorage.
 */
export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

/**
 * Clear stored tokens.
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Check if user is authenticated (has tokens).
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/**
 * Refresh the access token using the refresh token.
 */
export async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearTokens();
      return false;
    }

    const data = await response.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

/**
 * Make an authenticated API request.
 * Automatically refreshes token if needed.
 */
export async function apiRequest<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  // Add auth header if we have a token
  const accessToken = getAccessToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (accessToken) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${accessToken}`;
  }

  let response = await fetch(url, { ...options, headers });

  // If unauthorized, try to refresh token
  if (response.status === 401 && accessToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      // Retry with new token
      const newToken = getAccessToken();
      (headers as Record<string, string>)['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(url, { ...options, headers });
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * API methods for common operations.
 */
export const api = {
  /**
   * Get current user info.
   */
  async getCurrentUser() {
    return apiRequest<{
      id: string;
      email: string;
      display_name: string | null;
      avatar_url: string | null;
      timezone: string;
      created_at: string;
    }>('/api/v1/auth/me');
  },

  /**
   * Logout the current user.
   */
  async logout() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      return;
    }

    try {
      await apiRequest('/api/v1/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } finally {
      clearTokens();
    }
  },

  /**
   * Logout from all devices.
   */
  async logoutAll() {
    try {
      await apiRequest('/api/v1/auth/logout-all', { method: 'POST' });
    } finally {
      clearTokens();
    }
  },

  /**
   * Send a chat message.
   */
  async sendMessage(messages: Array<{ role: string; content: string }>) {
    return apiRequest<{ reply: string }>('/api/v1/chat/send', {
      method: 'POST',
      body: JSON.stringify({
        system: '',
        messages,
        stream: false,
      }),
    });
  },

  /**
   * Get chat history.
   */
  async getChatHistory() {
    return apiRequest<{ history: string }>('/api/v1/chat/history');
  },

  /**
   * Clear chat history.
   */
  async clearChatHistory() {
    return apiRequest('/api/v1/chat/history', { method: 'DELETE' });
  },

  /**
   * Set user timezone.
   */
  async setTimezone(timezone: string) {
    return apiRequest('/api/v1/meta/timezone', {
      method: 'POST',
      body: JSON.stringify({ timezone }),
    });
  },

  // ============================================
  // Wally Junior - Child API methods
  // ============================================

  /**
   * Verify an invite code (for child signup).
   */
  async verifyInviteCode(code: string) {
    return apiRequest<{
      valid: boolean;
      child_name: string;
      initial_balance: number;
    }>(`/api/v2/auth/child/verify-code?code=${encodeURIComponent(code)}`);
  },

  /**
   * Sign up as a child using invite code.
   */
  async childSignup(inviteCode: string, password: string) {
    return apiRequest<{
      access_token: string;
      refresh_token: string;
      expires_in: number;
    }>('/api/v2/auth/child/signup', {
      method: 'POST',
      body: JSON.stringify({ invite_code: inviteCode, password }),
    });
  },

  /**
   * Login as a child.
   */
  async childLogin(email: string, password: string) {
    return apiRequest<{
      access_token: string;
      refresh_token: string;
      expires_in: number;
    }>('/api/v2/auth/child/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  /**
   * Get child's current balance.
   */
  async getBalance() {
    const data = await apiRequest<{
      balance: number;
      balance_formatted: string;
    }>('/api/v2/finance/balance');
    // Map to expected format for frontend compatibility
    return {
      current_balance: data.balance,
      balance_formatted: data.balance_formatted,
    };
  },

  /**
   * Get child's dashboard stats.
   */
  async getDashboard() {
    return apiRequest<{
      balance: number;
      total_spent_today: number;
      total_spent_week: number;
      total_spent_month: number;
      active_goals_count: number;
      total_saved: number;
    }>('/api/v2/finance/dashboard');
  },

  /**
   * Get recent expenses.
   */
  async getExpenses(limit = 20) {
    return apiRequest<{
      expenses: Array<{
        id: number;
        amount: number;
        category: string;
        description: string | null;
        expense_date: string;
        created_at: string;
      }>;
      total: number;
    }>(`/api/v2/finance/expenses?limit=${limit}`);
  },

  /**
   * Log a new expense.
   */
  async logExpense(amount: number, category: string, description?: string) {
    return apiRequest<{ id: number; message: string }>('/api/v2/finance/expenses', {
      method: 'POST',
      body: JSON.stringify({ amount, category, description }),
    });
  },

  /**
   * Get spending summary.
   */
  async getSpendingSummary(period: 'today' | 'week' | 'month' = 'week') {
    return apiRequest<{
      period: string;
      total: number;
      by_category: Record<string, number>;
    }>(`/api/v2/finance/spending-summary?period=${period}`);
  },

  /**
   * Get savings goals (piggy banks).
   */
  async getSavingsGoals() {
    const goals = await apiRequest<Array<{
      id: number;
      name: string;
      target_amount: number;
      current_amount: number;
      status: string;
      emoji: string | null;
      created_at: string;
      completed_at: string | null;
    }>>('/api/v2/finance/goals');
    // Wrap array response to match expected format
    return { goals: goals || [] };
  },

  /**
   * Create a new savings goal.
   */
  async createSavingsGoal(name: string, targetAmount: number, emoji?: string) {
    return apiRequest<{ id: number; message: string }>('/api/v2/finance/goals', {
      method: 'POST',
      body: JSON.stringify({ name, target_amount: targetAmount, emoji }),
    });
  },

  /**
   * Add money to a savings goal.
   */
  async addToSavingsGoal(goalId: number, amount: number) {
    return apiRequest<{
      new_amount: number;
      completed: boolean;
      message: string;
    }>(`/api/v2/finance/goals/${goalId}/add`, {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
  },

  /**
   * Delete/abandon a savings goal.
   */
  async deleteSavingsGoal(goalId: number) {
    return apiRequest<{ message: string }>(`/api/v2/finance/goals/${goalId}`, {
      method: 'DELETE',
    });
  },

  // ============================================
  // Wally Junior - Parent API methods
  // ============================================

  /**
   * Create a child account (generates invite code).
   */
  async createChildAccount(childName: string, initialBalance: number) {
    const response = await apiRequest<{
      code: string;
      child_name: string;
      initial_balance: number;
      expires_at: string;
    }>('/api/v2/family/create-child', {
      method: 'POST',
      body: JSON.stringify({ child_name: childName, initial_balance: initialBalance }),
    });
    // Map 'code' to 'invite_code' for frontend compatibility
    return {
      invite_code: response.code,
      child_name: response.child_name,
      initial_balance: response.initial_balance,
      expires_at: response.expires_at,
    };
  },

  /**
   * Get parent's children.
   */
  async getChildren() {
    const children = await apiRequest<Array<{
      id: string;
      display_name: string | null;
      email: string;
      initial_balance: number;
      created_at: string;
    }>>('/api/v2/family/children');
    // Wrap in object for frontend compatibility
    return { children };
  },

  /**
   * Get a specific child's details.
   */
  async getChildDetails(childId: string) {
    return apiRequest<{
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
    }>(`/api/v2/family/child/${childId}`);
  },

  /**
   * Get pending invite codes.
   */
  async getPendingInvites() {
    const invites = await apiRequest<Array<{
      id: number;
      code: string;
      child_name: string;
      initial_balance: number;
      expires_at: string;
      created_at: string;
    }>>('/api/v2/family/invites');
    // Wrap in object for frontend compatibility
    return { invites };
  },

  /**
   * Cancel an invite code.
   */
  async cancelInvite(inviteId: number) {
    return apiRequest<{ message: string }>(`/api/v2/family/invite/${inviteId}`, {
      method: 'DELETE',
    });
  },

  // ============================================
  // Wally Junior - Achievements API methods
  // ============================================

  /**
   * Get all earned achievements.
   */
  async getEarnedAchievements() {
    return apiRequest<Array<{
      id: number;
      type: string;
      name: string;
      description: string;
      emoji: string;
      earned_at: string;
      metadata: Record<string, unknown>;
    }>>('/api/v2/achievements');
  },

  /**
   * Get all possible achievements with earned status.
   */
  async getAllAchievements() {
    return apiRequest<Array<{
      type: string;
      name: string;
      description: string;
      emoji: string;
      earned: boolean;
      earned_at: string | null;
    }>>('/api/v2/achievements/all');
  },

  /**
   * Get achievement progress summary.
   */
  async getAchievementProgress() {
    return apiRequest<{
      earned: number;
      total: number;
      progress_percent: number;
      remaining: number;
    }>('/api/v2/achievements/progress');
  },

  /**
   * Get achievement definitions (no auth required).
   */
  async getAchievementDefinitions() {
    return apiRequest<{
      achievements: Array<{
        type: string;
        name: string;
        description: string;
        emoji: string;
      }>;
      total: number;
    }>('/api/v2/achievements/definitions');
  },
};
