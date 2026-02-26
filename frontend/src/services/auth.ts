import { API_BASE_URL } from '../config/runtime';

const AUTH_BASE = `${API_BASE_URL}/auth`;

export type AuthUser = {
  id: string;
  username: string;
  role: 'admin' | 'analyst' | string;
  is_active: boolean;
  created_at?: string;
  last_login_at?: string | null;
};

function setToken(token: string, persist = true): void {
  if (persist) {
    localStorage.setItem('auth_token', token);
    sessionStorage.removeItem('auth_token');
  } else {
    sessionStorage.setItem('auth_token', token);
    localStorage.removeItem('auth_token');
  }
}

function getToken(): string | null {
  return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const authService = {
  async bootstrapStatus(): Promise<{ bootstrap_required: boolean }> {
    const response = await fetch(`${AUTH_BASE}/bootstrap-status`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to check bootstrap status');
    return data;
  },

  async bootstrap(username: string, password: string, persist = true): Promise<{ token: string; user: AuthUser }> {
    const response = await fetch(`${AUTH_BASE}/bootstrap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Bootstrap failed');
    setToken(data.token, persist);
    return data;
  },

  async login(username: string, password: string, persist = true): Promise<{ token: string; user: AuthUser }> {
    const response = await fetch(`${AUTH_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Login failed');
    setToken(data.token, persist);
    return data;
  },

  async me(): Promise<{ authenticated: boolean; user?: AuthUser }> {
    const response = await fetch(`${AUTH_BASE}/me`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to fetch user profile');
    return data;
  },

  async register(username: string, password: string, role: 'admin' | 'analyst' = 'analyst'): Promise<{ user: AuthUser }> {
    const response = await fetch(`${AUTH_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ username, password, role }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'User registration failed');
    return data;
  },

  async listUsers(): Promise<AuthUser[]> {
    const response = await fetch(`${AUTH_BASE}/users`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Failed to list users');
    return data;
  },

  logout(): void {
    localStorage.removeItem('auth_token');
    sessionStorage.removeItem('auth_token');
  },
};
