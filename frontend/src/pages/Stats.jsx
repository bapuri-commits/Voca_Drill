import { useEffect, useState } from 'react';
import { api } from '../api';

const LEVEL_COLORS = ['#64748b', '#ef4444', '#f97316', '#eab308', '#22c55e'];
const LEVEL_NAMES = ['New', 'Learning', 'Review', 'Familiar', 'Mastered'];

export default function Stats() {
  const [daily, setDaily] = useState(null);
  const [overall, setOverall] = useState(null);

  useEffect(() => {
    api.getDailyStats().then(setDaily).catch(() => {});
    api.getOverall().then(setOverall).catch(() => {});
  }, []);

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-xl font-bold mb-4">Stats</h1>

      {/* Daily */}
      {daily && (
        <div className="rounded-xl p-4 mb-4" style={{ background: 'var(--color-surface)' }}>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-dim)' }}>Today</h2>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Words Studied" value={daily.words_studied} />
            <StatCard label="Accuracy" value={`${Math.round(daily.correct_rate * 100)}%`} />
            <StatCard label="New Words" value={daily.new_words} />
            <StatCard label="Review" value={daily.review_words} />
            <StatCard label="Sessions" value={daily.sessions_count} />
            <StatCard label="Streak" value={`${daily.streak_days} days`} />
          </div>
        </div>
      )}

      {/* Overall Progress */}
      {overall && (
        <div className="rounded-xl p-4 mb-4" style={{ background: 'var(--color-surface)' }}>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-dim)' }}>
            Overall ({overall.studied_words}/{overall.total_words})
          </h2>

          {/* Level bars */}
          <div className="flex flex-col gap-2">
            {overall.level_distribution.map((lv, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-xs w-16" style={{ color: LEVEL_COLORS[i] }}>{LEVEL_NAMES[i]}</span>
                <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-light)' }}>
                  <div className="h-full rounded-full transition-all"
                       style={{ width: `${lv.percentage}%`, background: LEVEL_COLORS[i] }} />
                </div>
                <span className="text-xs w-8 text-right" style={{ color: 'var(--color-text-dim)' }}>{lv.count}</span>
              </div>
            ))}
          </div>

          {overall.estimated_days_remaining > 0 && (
            <div className="mt-3 text-xs text-center" style={{ color: 'var(--color-text-dim)' }}>
              Estimated completion: ~{overall.estimated_days_remaining} days
            </div>
          )}
        </div>
      )}

      {/* Chapter Progress */}
      {overall?.chapter_progress?.length > 0 && (
        <div className="rounded-xl p-4" style={{ background: 'var(--color-surface)' }}>
          <h2 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-dim)' }}>By Chapter</h2>
          <div className="flex flex-col gap-2">
            {overall.chapter_progress.map((ch, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="text-xs w-14" style={{ color: 'var(--color-text-dim)' }}>{ch.chapter}</span>
                <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-light)' }}>
                  <div className="h-full rounded-full" style={{ width: `${ch.completion_rate}%`, background: 'var(--color-primary)' }} />
                </div>
                <span className="text-xs w-12 text-right" style={{ color: 'var(--color-text-dim)' }}>
                  {ch.studied}/{ch.total}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-lg p-3 text-center" style={{ background: 'var(--color-surface-light)' }}>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs" style={{ color: 'var(--color-text-dim)' }}>{label}</div>
    </div>
  );
}
