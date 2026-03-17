import { useEffect, useState } from 'react';
import { api } from '../api';

export default function PdfViewer() {
  const [pdfs, setPdfs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listPdfs()
      .then(list => {
        setPdfs(list);
        if (list.length > 0) setSelected(list[0].filename);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="w-8 h-8 rounded-full border-3 border-t-transparent animate-spin"
             style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  if (pdfs.length === 0) {
    return (
      <div className="max-w-md mx-auto p-4">
        <h1 className="text-xl font-bold mb-4">Book</h1>
        <div className="rounded-2xl p-8 text-center" style={{ background: 'var(--color-surface)' }}>
          <div className="text-4xl mb-3">📚</div>
          <p className="text-sm" style={{ color: 'var(--color-text-dim)' }}>
            PDF 파일이 없습니다.
          </p>
          <p className="text-xs mt-2" style={{ color: 'var(--color-text-dim)', opacity: 0.6 }}>
            서버의 data/pdf/ 디렉토리에 PDF를 추가하세요.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold">Book</h1>
        {pdfs.length > 1 && (
          <select
            value={selected || ''}
            onChange={e => setSelected(e.target.value)}
            className="px-3 py-1.5 rounded-lg text-sm border-none"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text)' }}
          >
            {pdfs.map(p => (
              <option key={p.filename} value={p.filename}>
                {p.filename} ({p.size_mb} MB)
              </option>
            ))}
          </select>
        )}
      </div>

      {selected && (
        <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--color-surface)' }}>
          <iframe
            src={`/api/pdf/${encodeURIComponent(selected)}?token=${localStorage.getItem('voca_token') || ''}`}
            className="w-full border-none"
            style={{ height: 'calc(100vh - 180px)', minHeight: '500px' }}
            title="PDF Viewer"
          />
        </div>
      )}
    </div>
  );
}
