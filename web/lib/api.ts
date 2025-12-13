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
   * Get Gmail connection status.
   */
  async getGmailStatus(userId: string, connectionRequestId: string) {
    return apiRequest<{
      ok: boolean;
      connected: boolean;
      status?: string;
      email?: string;
    }>('/api/v1/gmail/status', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, connection_request_id: connectionRequestId }),
    });
  },

  /**
   * Initiate Gmail connection.
   */
  async connectGmail(userId: string) {
    return apiRequest<{
      ok: boolean;
      redirect_url?: string;
      connection_request_id?: string;
    }>('/api/v1/gmail/connect', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  },

  /**
   * Disconnect Gmail.
   */
  async disconnectGmail(userId: string, connectionId?: string, connectionRequestId?: string) {
    return apiRequest('/api/v1/gmail/disconnect', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        connection_id: connectionId,
        connection_request_id: connectionRequestId,
      }),
    });
  },

  /**
   * Get Calendar connection status.
   */
  async getCalendarStatus(userId: string, connectionRequestId: string) {
    return apiRequest<{
      ok: boolean;
      connected: boolean;
      status?: string;
      email?: string;
    }>('/api/v1/calendar/status', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, connection_request_id: connectionRequestId }),
    });
  },

  /**
   * Initiate Calendar connection.
   */
  async connectCalendar(userId: string) {
    return apiRequest<{
      ok: boolean;
      redirect_url?: string;
      connection_request_id?: string;
    }>('/api/v1/calendar/connect', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  },

  /**
   * Disconnect Calendar.
   */
  async disconnectCalendar(userId: string, connectionId?: string, connectionRequestId?: string) {
    return apiRequest('/api/v1/calendar/disconnect', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        connection_id: connectionId,
        connection_request_id: connectionRequestId,
      }),
    });
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
};
