import { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

const AuthContext = createContext(null);

const SYOPS_AUTH = import.meta.env.DEV ? 'https://syworkspace.cloud/api/auth' : '/syops-auth';
const SYOPS_LOGIN = 'https://syworkspace.cloud/login';

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const tokenRef = useRef(token);
  const refreshPromiseRef = useRef(null);

  useEffect(() => { tokenRef.current = token; }, [token]);

  const fetchUserInfo = useCallback(async (accessToken) => {
    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return res?.ok;
    } catch { return false; }
  }, []);

  const refreshAccessToken = useCallback(async () => {
    if (refreshPromiseRef.current) return refreshPromiseRef.current;
    const promise = (async () => {
      try {
        const res = await fetch(`${SYOPS_AUTH}/refresh`, {
          method: 'POST',
          credentials: 'include',
        });
        if (res.ok) {
          const data = await res.json();
          setToken(data.access_token);
          return data.access_token;
        }
      } catch { /* network error */ }
      setToken(null);
      return null;
    })();
    refreshPromiseRef.current = promise;
    promise.finally(() => { refreshPromiseRef.current = null; });
    return promise;
  }, []);

  useEffect(() => {
    refreshAccessToken().finally(() => setInitializing(false));
  }, [refreshAccessToken]);

  const login = useCallback(async (username, password) => {
    const res = await fetch(`${SYOPS_AUTH}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();
    setToken(data.access_token);
    return true;
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch(`${SYOPS_AUTH}/logout`, { method: 'POST', credentials: 'include' });
    } catch { /* ignore */ }
    setToken(null);
  }, []);

  const authFetch = useCallback(async (url, options = {}) => {
    const doFetch = (t) =>
      fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
          ...(t ? { Authorization: `Bearer ${t}` } : {}),
        },
      });

    let res = await doFetch(tokenRef.current);

    if (res.status === 401) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        res = await doFetch(newToken);
      } else {
        window.location.href = SYOPS_LOGIN + '?redirect=' + encodeURIComponent(window.location.href);
      }
    }

    return res;
  }, [refreshAccessToken]);

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
