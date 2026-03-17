import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

export default function StudyHome() {
  const nav = useNavigate();
  const [view, setView] = useState('modes');
  const [chapters, setChapters] = useState([]);
  const [reviewCount, setReviewCount] = useState(null);
  const [bookTestCount, setBookTestCount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chaptersLoading, setChaptersLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getReviewCount().catch(() => ({ count: 0 })),
      api.getBookTests().catch(() => []),
    ]).then(([review, tests]) => {
      setReviewCount(review.count);
      setBookTestCount(tests.length);
      setLoading(false);
    });
  }, []);

  const openDaySelect = async () => {
    setChaptersLoading(true);
    try {
      const data = await api.getChapterProgress();
      setChapters(data);
    } catch {}
    setChaptersLoading(false);
    setView('day-select');
  };

  const startQuickStudy = () => {
    if (reviewCount === 0) return;
    nav('/study/session?mode=review');
  };

  if (loading) {
    return (
      <div className="max-w-md mx-auto p-4">
        <h1 className="text-xl font-bold mb-6">Study</h1>
        <Spinner />
      </div>
    );
  }

  if (view === 'day-select') {
    return (
      <div className="max-w-md mx-auto p-4">
        <div className="flex items-center gap-3 mb-6">
          <button
            onClick={() => setView('modes')}
            className="w-8 h-8 rounded-full flex items-center justify-center border-none cursor-pointer text-base"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text)' }}
          >
            ←
          </button>
          <h1 className="text-xl font-bold">Select Day</h1>
        </div>

        {chaptersLoading ? (
          <Spinner />
        ) : (
          <div className="flex flex-col gap-3">
            {chapters.map(ch => (
              <button
                key={ch.chapter}
                onClick={() => nav(`/study/session?mode=day&chapter=${encodeURIComponent(ch.chapter)}`)}
                className="w-full p-4 rounded-xl border-none cursor-pointer text-left transition-transform active:scale-[0.98]"
                style={{ background: 'var(--color-surface)' }}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold">{ch.chapter}</span>
                  <span className="text-xs" style={{ color: 'var(--color-text-dim)' }}>
                    {ch.studied}/{ch.total}
                  </span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-light)' }}>
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${ch.completion_rate}%`,
                      background: ch.completion_rate >= 100 ? '#22c55e' : 'var(--color-primary)',
                    }}
                  />
                </div>
                {ch.completion_rate >= 100 && (
                  <div className="text-xs mt-1.5 font-semibold" style={{ color: '#22c55e' }}>
                    ✓ Complete
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-xl font-bold mb-6">Study</h1>

      <div className="flex flex-col gap-4">
        <ModeCard
          icon="📖"
          title="Day Study"
          desc="Day 단위로 전체 단어 학습"
          onClick={openDaySelect}
        />

        <ModeCard
          icon="⚡"
          title="Quick Study"
          desc={
            reviewCount === 0
              ? '복습 대상 없음 — Day 학습을 먼저 완료하세요'
              : `${reviewCount}개 단어 복습 가능`
          }
          onClick={startQuickStudy}
          disabled={reviewCount === 0}
          badge={reviewCount > 0 ? reviewCount : null}
        />

        <ModeCard
          icon="📝"
          title="Book Test"
          desc={bookTestCount != null ? `${bookTestCount}개 교재 테스트` : '교재 테스트 풀기'}
          onClick={() => nav('/study/book-test')}
        />
      </div>
    </div>
  );
}

function ModeCard({ icon, title, desc, onClick, disabled, badge }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full p-5 rounded-2xl border-none cursor-pointer text-left transition-transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-default"
      style={{ background: 'var(--color-surface)' }}
    >
      <div className="flex items-center gap-4">
        <div className="text-3xl">{icon}</div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg">{title}</span>
            {badge != null && (
              <span
                className="px-2 py-0.5 rounded-full text-xs font-bold text-white"
                style={{ background: 'var(--color-primary)' }}
              >
                {badge}
              </span>
            )}
          </div>
          <div className="text-sm mt-0.5" style={{ color: 'var(--color-text-dim)' }}>
            {desc}
          </div>
        </div>
        {!disabled && (
          <span className="text-lg" style={{ color: 'var(--color-text-dim)' }}>›</span>
        )}
      </div>
    </button>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div
        className="w-8 h-8 rounded-full border-3 border-t-transparent animate-spin"
        style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }}
      />
    </div>
  );
}
