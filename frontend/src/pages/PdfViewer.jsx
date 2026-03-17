import { useEffect, useState } from 'react';
import { api } from '../api';

const TOKEN_KEY = 'voca_token';

export default function PdfViewer() {
  const [data, setData] = useState(null);
  const [mode, setMode] = useState('day');
  const [selected, setSelected] = useState(null);
  const [showFullWarning, setShowFullWarning] = useState(false);
  const [loadingFull, setLoadingFull] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listPdfs()
      .then(d => {
        setData(d);
        if (d.day?.length > 0) setSelected(d.day[0].filename);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const token = localStorage.getItem(TOKEN_KEY) || '';
  const pdfUrl = (filename) => `/api/pdf/${filename}?token=${token}`;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 rounded-full border-3 border-t-transparent animate-spin"
             style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  const hasDays = data?.day?.length > 0;
  const hasTests = data?.test?.length > 0;
  const hasFull = data?.full?.length > 0;

  if (!hasDays && !hasTests && !hasFull) {
    return (
      <div className="max-w-md mx-auto p-4">
        <h1 className="text-xl font-bold mb-4">Book</h1>
        <div className="rounded-2xl p-8 text-center" style={{ background: 'var(--color-surface)' }}>
          <div className="text-4xl mb-3">📚</div>
          <p className="text-sm" style={{ color: 'var(--color-text-dim)' }}>PDF 파일이 없습니다.</p>
        </div>
      </div>
    );
  }

  const switchMode = (m) => {
    if (m === 'full') {
      setShowFullWarning(true);
      return;
    }
    setMode(m);
    setLoadingFull(false);
    const list = m === 'day' ? data.day : data.test;
    if (list?.length > 0) setSelected(list[0].filename);
  };

  const currentList = mode === 'day' ? data?.day : mode === 'test' ? data?.test : [];

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Header + Mode Toggle */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Book</h1>
        <div className="flex gap-1.5">
          {hasDays && <ModeBtn label="Day" active={mode === 'day'} onClick={() => switchMode('day')} />}
          {hasTests && <ModeBtn label="Test" active={mode === 'test'} onClick={() => switchMode('test')} />}
          {hasFull && <ModeBtn label="전체" active={mode === 'full'} onClick={() => switchMode('full')} />}
        </div>
      </div>

      {/* Day / Test Selector */}
      {(mode === 'day' || mode === 'test') && currentList?.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-3 mb-3">
          {currentList.map(d => (
            <button
              key={d.filename}
              onClick={() => setSelected(d.filename)}
              className="px-3 py-2 rounded-lg text-xs whitespace-nowrap border-none cursor-pointer transition-colors flex-shrink-0"
              style={{
                background: selected === d.filename ? 'var(--color-primary)' : 'var(--color-surface)',
                color: selected === d.filename ? '#fff' : 'var(--color-text-dim)',
              }}
            >
              {d.label}
            </button>
          ))}
        </div>
      )}

      {/* PDF iframe (Day / Test) */}
      {(mode === 'day' || mode === 'test') && selected && (
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--color-surface)' }}>
          <iframe
            key={selected}
            src={pdfUrl(selected)}
            className="w-full border-none"
            style={{ height: 'calc(100vh - 220px)', minHeight: '500px' }}
            title="PDF Viewer"
          />
        </div>
      )}

      {/* Full PDF Warning Modal */}
      {showFullWarning && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6"
             style={{ background: 'rgba(0,0,0,0.7)' }}
             onClick={() => setShowFullWarning(false)}>
          <div className="w-full max-w-xs rounded-2xl p-6 text-center"
               style={{ background: 'var(--color-surface)' }}
               onClick={e => e.stopPropagation()}>
            <div className="text-3xl mb-3">📚</div>
            <h2 className="text-lg font-bold mb-2">전체 PDF 로드</h2>
            <p className="text-sm mb-1" style={{ color: 'var(--color-text-dim)' }}>
              {data.full[0]?.size_mb || 300}MB 파일을 로드합니다.
            </p>
            <p className="text-xs mb-5" style={{ color: 'var(--color-text-dim)', opacity: 0.6 }}>
              네트워크 상태에 따라 1~3분 소요될 수 있습니다.
            </p>
            <div className="flex gap-3">
              <button onClick={() => setShowFullWarning(false)}
                className="flex-1 py-2.5 rounded-xl text-sm border-none cursor-pointer"
                style={{ background: 'var(--color-surface-light)', color: 'var(--color-text-dim)' }}>
                취소
              </button>
              <button onClick={() => { setMode('full'); setLoadingFull(true); setShowFullWarning(false); }}
                className="flex-1 py-2.5 rounded-xl text-sm font-bold border-none cursor-pointer"
                style={{ background: 'var(--color-primary)', color: '#fff' }}>
                로드
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Full PDF */}
      {mode === 'full' && hasFull && (
        <>
          {loadingFull && (
            <div className="flex items-center justify-center py-8 gap-3">
              <div className="w-6 h-6 rounded-full border-3 border-t-transparent animate-spin"
                   style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }} />
              <span className="text-sm" style={{ color: 'var(--color-text-dim)' }}>
                전체 PDF 로딩 중... ({data.full[0]?.size_mb}MB)
              </span>
            </div>
          )}
          <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--color-surface)' }}>
            <iframe
              src={pdfUrl(data.full[0].filename)}
              className="w-full border-none"
              style={{ height: 'calc(100vh - 180px)', minHeight: '500px' }}
              title="Full PDF"
              onLoad={() => setLoadingFull(false)}
            />
          </div>
        </>
      )}
    </div>
  );
}

function ModeBtn({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 rounded-lg text-xs border-none cursor-pointer transition-colors"
      style={{
        background: active ? 'var(--color-primary)' : 'var(--color-surface-light)',
        color: active ? '#fff' : 'var(--color-text-dim)',
      }}
    >
      {label}
    </button>
  );
}
