import { useEffect, useState } from 'react';
import { api } from '../api';

const LEVEL_COLORS = ['#64748b', '#ef4444', '#f97316', '#eab308', '#22c55e'];
const LEVEL_NAMES = ['New', 'Learning', 'Review', 'Familiar', 'Mastered'];

export default function Stats() {
  const [daily, setDaily] = useState(null);
  const [overall, setOverall] = useState(null);
  const [backups, setBackups] = useState([]);
  const [backupLoading, setBackupLoading] = useState(false);
  const [backupMsg, setBackupMsg] = useState(null);
  const [showBackups, setShowBackups] = useState(false);
  const [confirmRestore, setConfirmRestore] = useState(null);

  useEffect(() => {
    api.getDailyStats().then(setDaily).catch(() => {});
    api.getOverall().then(setOverall).catch(() => {});
  }, []);

  const loadBackups = async () => {
    if (!showBackups) {
      setShowBackups(true);
      try {
        const data = await api.listBackups();
        setBackups(data);
      } catch {}
    } else {
      setShowBackups(false);
    }
  };

  const handleCreateBackup = async () => {
    setBackupLoading(true);
    setBackupMsg(null);
    try {
      const res = await api.createBackup();
      setBackupMsg(`백업 생성: ${res.filename} (${res.size_mb}MB)`);
      const data = await api.listBackups();
      setBackups(data);
    } catch (e) {
      setBackupMsg(`오류: ${e.message}`);
    }
    setBackupLoading(false);
  };

  const handleRestore = async (filename) => {
    setConfirmRestore(null);
    setBackupLoading(true);
    setBackupMsg(null);
    try {
      const res = await api.restoreBackup(filename);
      setBackupMsg(`복원 완료: ${res.restored}`);
      const data = await api.listBackups();
      setBackups(data);
    } catch (e) {
      setBackupMsg(`복원 오류: ${e.message}`);
    }
    setBackupLoading(false);
  };

  const handleDelete = async (filename) => {
    try {
      await api.deleteBackup(filename);
      setBackups(prev => prev.filter(b => b.filename !== filename));
    } catch {}
  };

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
        <div className="rounded-xl p-4 mb-4" style={{ background: 'var(--color-surface)' }}>
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

      {/* Data Management */}
      <div className="rounded-xl p-4" style={{ background: 'var(--color-surface)' }}>
        <div className="flex justify-between items-center mb-3">
          <h2 className="text-sm font-semibold" style={{ color: 'var(--color-text-dim)' }}>Data</h2>
          <button
            onClick={loadBackups}
            className="text-xs px-3 py-1 rounded-lg border-none cursor-pointer"
            style={{ background: 'var(--color-surface-light)', color: 'var(--color-text-dim)' }}
          >
            {showBackups ? 'Hide' : 'Backup'}
          </button>
        </div>

        {showBackups && (
          <>
            <button
              onClick={handleCreateBackup}
              disabled={backupLoading}
              className="w-full py-2.5 rounded-lg border-none cursor-pointer text-sm font-semibold mb-3 transition-transform active:scale-95 disabled:opacity-50"
              style={{ background: 'var(--color-primary)', color: '#fff' }}
            >
              {backupLoading ? 'Processing...' : 'Create Backup'}
            </button>

            {backupMsg && (
              <div className="text-xs p-2 rounded-lg mb-3"
                   style={{ background: 'var(--color-surface-light)', color: 'var(--color-text-dim)' }}>
                {backupMsg}
              </div>
            )}

            {backups.length === 0 ? (
              <div className="text-xs text-center py-3" style={{ color: 'var(--color-text-dim)' }}>
                No backups yet
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {backups.map(b => (
                  <div key={b.filename} className="flex items-center gap-2 p-2 rounded-lg"
                       style={{ background: 'var(--color-surface-light)' }}>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold truncate">{b.filename}</div>
                      <div className="text-xs" style={{ color: 'var(--color-text-dim)' }}>
                        {b.size_mb}MB · {new Date(b.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button
                      onClick={() => setConfirmRestore(b.filename)}
                      className="text-xs px-2 py-1 rounded border-none cursor-pointer"
                      style={{ background: 'var(--color-primary)', color: '#fff' }}
                    >
                      Restore
                    </button>
                    <button
                      onClick={() => handleDelete(b.filename)}
                      className="text-xs px-2 py-1 rounded border-none cursor-pointer"
                      style={{ background: 'rgba(239,68,68,0.2)', color: '#ef4444' }}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Restore Confirm Modal */}
      {confirmRestore && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6"
             style={{ background: 'rgba(0,0,0,0.7)' }}
             onClick={() => setConfirmRestore(null)}>
          <div className="w-full max-w-xs rounded-2xl p-6 text-center"
               style={{ background: 'var(--color-surface)' }}
               onClick={e => e.stopPropagation()}>
            <div className="text-3xl mb-3">⚠️</div>
            <h2 className="text-lg font-bold mb-2">Restore Backup?</h2>
            <p className="text-sm mb-4" style={{ color: 'var(--color-text-dim)' }}>
              현재 데이터가 백업으로 교체됩니다.<br />
              복원 전 자동으로 현재 상태가 백업됩니다.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmRestore(null)}
                className="flex-1 py-2.5 rounded-xl text-sm border-none cursor-pointer"
                style={{ background: 'var(--color-surface-light)', color: 'var(--color-text-dim)' }}
              >
                Cancel
              </button>
              <button
                onClick={() => handleRestore(confirmRestore)}
                className="flex-1 py-2.5 rounded-xl text-sm font-bold border-none cursor-pointer"
                style={{ background: '#ef4444', color: '#fff' }}
              >
                Restore
              </button>
            </div>
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
