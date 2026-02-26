import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { authService, AuthUser } from '../services/auth';

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (username: string, password: string, persist?: boolean) => Promise<void>;
  bootstrap: (username: string, password: string, persist?: boolean) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const me = await authService.me();
      setUser(me.authenticated ? me.user || null : null);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    (async () => {
      await refresh();
      setLoading(false);
    })();
  }, [refresh]);

  const login = useCallback(async (username: string, password: string, persist = true) => {
    const result = await authService.login(username, password, persist);
    setUser(result.user);
  }, []);

  const bootstrap = useCallback(async (username: string, password: string, persist = true) => {
    const result = await authService.bootstrap(username, password, persist);
    setUser(result.user);
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      loading,
      login,
      bootstrap,
      logout,
      refresh,
    }),
    [user, loading, login, bootstrap, logout, refresh]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
