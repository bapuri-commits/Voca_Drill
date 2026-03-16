import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

const LEVEL_COLORS = ['#64748b', '#ef4444', '#f97316', '#eab308', '#22c55e'];
const LEVEL_NAMES = ['New', 'Learning', 'Review', 'Familiar', 'Mastered'];

export default function Dashboard() {
  const nav = useNavigate();
  const [daily, setDaily] = useState(null);
  const [overall, setOverall] = useState(null);

  useEffect(() => {
    api.getDailyStats().then(setDaily).catch(() => {});
    api.getOverall().then(setOverall).catch(() => {});
  }, []);

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6 text-center">Voca Drill</h1>

      {/* Start Button */}
      <button
        onClick={() => nav('/study')}
        className="w-full py-4 rounded-2xl text-xl font-bold mb-6 cursor-pointer border-none transition-transform active:scale-95"
        style={{ background: 'var(--color-primary)', color: '#fff' }}
      >
        Start Study
      </button>

      {/* Daily Stats */}
      {daily && (
        <div className="rounded-xl p-4 mb-4" style={{ background: 'var(--color-surface)' }}>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-dim)' }}>Today</h2>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-2xl font-bold">{daily.words_studied}</div>
              <div className="text-xs" style={{ color: 'var(--color-text-dim)' }}>Words</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{Math.round(daily.correct_rate * 100)}%</div>
              <div className="text-xs" style={{ color: 'var(--color-text-dim)' }}>Accuracy</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{daily.streak_days}</div>
              <div className="text-xs" style={{ color: 'var(--color-text-dim)' }}>Streak</div>
            </div>
          </div>
        </div>
      )}

      {/* Level Distribution */}
      {overall && (
        <div className="rounded-xl p-4" style={{ background: 'var(--color-surface)' }}>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-dim)' }}>
            Progress ({overall.studied_words}/{overall.total_words})
          </h2>

          {/* Bar */}
          <div className="flex rounded-full overflow-hidden h-4 mb-3" style={{ background: 'var(--color-surface-light)' }}>
            {overall.level_distribution.map((lv, i) => (
              lv.percentage > 0 && (
                <div key={i} style={{ width: `${lv.percentage}%`, background: LEVEL_COLORS[i] }}
                     title={`${LEVEL_NAMES[i]}: ${lv.count}`} />
              )
            ))}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 text-xs">
            {overall.level_distribution.map((lv, i) => (
              <div key={i} className="flex items-center gap-1">
                <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: LEVEL_COLORS[i] }} />
                <span style={{ color: 'var(--color-text-dim)' }}>{LEVEL_NAMES[i]}: {lv.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
