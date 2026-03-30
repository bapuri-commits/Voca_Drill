import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

const LEVEL_COLORS = ['#94a3b8', '#ef4444', '#f97316', '#eab308', '#22c55e'];
const LEVEL_NAMES = ['New', 'Learning', 'Review', 'Familiar', 'Mastered'];

export default function Dashboard({ onLogout }) {
  const nav = useNavigate();
  const [daily, setDaily] = useState(null);
  const [overall, setOverall] = useState(null);

  useEffect(() => {
    api.getDailyStats().then(setDaily).catch(() => {});
    api.getOverall().then(setOverall).catch(() => {});
  }, []);

  return (
    <div className="max-w-md mx-auto p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>Voca Drill</h1>
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-dim)' }}>
            TOEFL Vocabulary Trainer
          </p>
        </div>
        {daily && daily.streak_days > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
               style={{ background: 'var(--color-warning-bg)', color: 'var(--color-warning)' }}>
            <span className="text-lg">🔥</span>
            <span className="text-sm font-bold">{daily.streak_days}</span>
          </div>
        )}
      </div>

      {/* Start Study */}
      <button
        onClick={() => nav('/study')}
        className="w-full py-5 rounded-2xl text-xl font-bold mb-6 cursor-pointer border-none transition-transform active:scale-[0.98]"
        style={{ background: 'var(--color-primary)', color: '#fff' }}
      >
        Start Study
      </button>

      {/* Today Stats */}
      {daily && (
        <div className="rounded-2xl p-4 mb-4" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <h2 className="text-xs font-semibold uppercase tracking-wider mb-3"
              style={{ color: 'var(--color-text-dim)' }}>Today</h2>
          <div className="grid grid-cols-3 gap-3 text-center">
            <QuickStat value={daily.words_studied} label="Words" />
            <QuickStat value={`${Math.round(daily.correct_rate * 100)}%`} label="Accuracy" />
            <QuickStat value={daily.sessions_count} label="Sessions" />
          </div>
        </div>
      )}

      {/* Progress Overview */}
      {overall && overall.total_words > 0 && (
        <div className="rounded-2xl p-4 mb-4" style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)' }}>
          <div className="flex justify-between items-baseline mb-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider"
                style={{ color: 'var(--color-text-dim)' }}>Progress</h2>
            <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
              {overall.studied_words} / {overall.total_words}
            </span>
          </div>

          <div className="flex rounded-full overflow-hidden h-3 mb-3"
               style={{ background: 'var(--color-surface-alt)' }}>
            {overall.level_distribution.map((lv, i) => (
              lv.percentage > 0 && (
                <div key={i} style={{ width: `${lv.percentage}%`, background: LEVEL_COLORS[i] }} />
              )
            ))}
          </div>

          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {overall.level_distribution.map((lv, i) => (
              lv.count > 0 && (
                <div key={i} className="flex items-center gap-1">
                  <span className="inline-block w-2 h-2 rounded-full" style={{ background: LEVEL_COLORS[i] }} />
                  <span style={{ color: 'var(--color-text-secondary)' }}>{LEVEL_NAMES[i]} {lv.count}</span>
                </div>
              )
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <ActionCard icon="📝" label="Words" sub={overall ? `${overall.total_words} total` : ''} onClick={() => nav('/words')} />
        <ActionCard icon="📚" label="Book" sub="PDF Viewer" onClick={() => nav('/pdf')} />
      </div>

      {/* Logout */}
      <button
        onClick={onLogout}
        className="w-full py-2.5 rounded-xl text-sm border-none cursor-pointer"
        style={{ background: 'var(--color-surface-alt)', color: 'var(--color-text-dim)' }}
      >
        Logout
      </button>
    </div>
  );
}

function QuickStat({ value, label }) {
  return (
    <div>
      <div className="text-2xl font-bold" style={{ color: 'var(--color-text)' }}>{value}</div>
      <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-dim)' }}>{label}</div>
    </div>
  );
}

function ActionCard({ icon, label, sub, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 p-4 rounded-xl cursor-pointer text-left transition-transform active:scale-[0.98] w-full"
      style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text)' }}
    >
      <span className="text-2xl">{icon}</span>
      <div>
        <div className="text-sm font-semibold">{label}</div>
        {sub && <div className="text-xs" style={{ color: 'var(--color-text-dim)' }}>{sub}</div>}
      </div>
    </button>
  );
}
