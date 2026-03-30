import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

const ERROR_MESSAGES = {
  'Invalid credentials': '아이디 또는 비밀번호가 틀렸습니다.',
  'Token expired': '세션이 만료되었습니다. 다시 로그인해주세요.',
  'Failed to fetch': '서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.',
};

function friendlyError(msg) {
  return ERROR_MESSAGES[msg] || msg || '로그인에 실패했습니다.';
}

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true);
    setError('');
    try {
      await login(username, password);
    } catch (err) {
      const msg = friendlyError(err.message);
      setError(msg);
      setShake(true);
      setTimeout(() => setShake(false), 500);
    }
    setLoading(false);
  };

  const inputBorder = error ? '2px solid var(--color-danger)' : '1px solid var(--color-border)';

  return (
    <div className="fixed inset-0 flex items-center justify-center p-6"
         style={{ background: 'var(--color-bg)' }}>
      <div className="w-full max-w-xs"
           style={{ animation: shake ? 'shake 0.5s ease-in-out' : 'none' }}>
        <h1 className="text-3xl font-bold text-center mb-2">Voca Drill</h1>
        <p className="text-sm text-center mb-8" style={{ color: 'var(--color-text-dim)' }}>
          SyOps 계정으로 로그인
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => { setUsername(e.target.value); setError(''); }}
            autoComplete="username"
            className="w-full px-4 py-3 rounded-xl text-base outline-none transition-all"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text)', border: inputBorder }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => { setPassword(e.target.value); setError(''); }}
            autoComplete="current-password"
            className="w-full px-4 py-3 rounded-xl text-base outline-none transition-all"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text)', border: inputBorder }}
          />

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm"
                 style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-danger)' }}>
              <span className="text-base">!</span>
              <span>{error}</span>
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

        <style>{`
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            20%, 60% { transform: translateX(-8px); }
            40%, 80% { transform: translateX(8px); }
          }
        `}</style>
      </div>
    </div>
  );
}
