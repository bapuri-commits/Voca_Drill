import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true);
    setError('');
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message || 'Login failed');
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center p-6"
         style={{ background: 'var(--color-bg)' }}>
      <div className="w-full max-w-xs">
        <h1 className="text-3xl font-bold text-center mb-2">Voca Drill</h1>
        <p className="text-sm text-center mb-8" style={{ color: 'var(--color-text-dim)' }}>
          SyOps 계정으로 로그인
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            autoComplete="username"
            className="w-full px-4 py-3 rounded-xl text-base border-none outline-none"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text)' }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            autoComplete="current-password"
            className="w-full px-4 py-3 rounded-xl text-base border-none outline-none"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text)' }}
          />

          {error && (
            <div className="text-sm text-center py-2" style={{ color: 'var(--color-danger)' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username || !password}
            className="w-full py-3.5 rounded-xl text-base font-bold border-none cursor-pointer transition-transform active:scale-95 disabled:opacity-50"
            style={{ background: 'var(--color-primary)', color: '#fff' }}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
}
