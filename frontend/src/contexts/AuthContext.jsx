import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

const AuthContext = createContext(null);

const SYOPS_AUTH = import.meta.env.DEV ? 'https://syworkspace.cloud/api/auth' : '/syops-auth';
const TOKEN_KEY = 'voca_token';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [initializing, setInitializing] = useState(true);
  const tokenRef = useRef(token);

  useEffect(() => { tokenRef.current = token; }, [token]);

  useEffect(() => {
    if (!token) {
      setInitializing(false);
      return;
    }
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(res => {
        if (!res.ok) {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
        }
      })
      .catch(() => {})
      .finally(() => setInitializing(false));
  }, []);

  const login = useCallback(async (username, password) => {
    const res = await fetch(`${SYOPS_AUTH}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    const accessToken = data.access_token;
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
    return true;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }, []);

  const authFetch = useCallback(async (url, options = {}) => {
    const doFetch = (t) =>
      fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
          ...(t ? { Authorization: `Bearer ${t}` } : {}),
        },
      });

    const res = await doFetch(tokenRef.current);

    if (res.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
    }

    return res;
  }, []);

  const authenticated = !!token;

  return (
    <AuthContext.Provider value={{ authenticated, initializing, login, logout, authFetch, token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be inside AuthProvider');
  return ctx;
}
