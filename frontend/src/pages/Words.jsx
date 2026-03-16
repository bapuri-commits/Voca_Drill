import { useEffect, useState } from 'react';
import { api } from '../api';

export default function Words() {
  const [words, setWords] = useState([]);
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState('');
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    api.getChapters().then(setChapters).catch(() => {});
  }, []);

  useEffect(() => {
    const params = { limit: 100 };
    if (selectedChapter) params.chapter = selectedChapter;
    api.getWords(params).then(setWords).catch(() => {});
  }, [selectedChapter]);

  return (
    <div className="max-w-md mx-auto p-4">
      <h1 className="text-xl font-bold mb-4">Words</h1>

      {/* Chapter Filter */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
        <Chip label="All" active={!selectedChapter} onClick={() => setSelectedChapter('')} />
        {chapters.map(ch => (
          <Chip key={ch.chapter} label={`${ch.chapter} (${ch.count})`}
                active={selectedChapter === ch.chapter}
                onClick={() => setSelectedChapter(ch.chapter)} />
        ))}
      </div>

      {/* Word List */}
      <div className="flex flex-col gap-2">
        {words.map(w => (
          <div key={w.id} className="rounded-xl p-3 cursor-pointer transition-colors"
               style={{ background: 'var(--color-surface)' }}
               onClick={() => setExpanded(expanded === w.id ? null : w.id)}>
            <div className="flex items-center justify-between">
              <div>
                <span className="font-bold mr-2">{w.english}</span>
                <span className="text-xs" style={{ color: 'var(--color-text-dim)' }}>
                  {'*'.repeat(w.frequency)}
                </span>
              </div>
              <span className="text-xs" style={{ color: 'var(--color-text-dim)' }}>
                {w.meanings[0]?.korean}
              </span>
            </div>

            {/* Tested Synonyms Preview */}
            {w.meanings[0]?.tested_synonyms?.length > 0 && (
              <div className="text-xs mt-1" style={{ color: 'var(--color-primary)' }}>
                {w.meanings[0].tested_synonyms.slice(0, 3).join(', ')}
                {w.meanings[0].tested_synonyms.length > 3 && ' ...'}
              </div>
            )}

            {/* Expanded Detail */}
            {expanded === w.id && (
              <div className="mt-3 pt-3" style={{ borderTop: '1px solid var(--color-surface-light)' }}>
                {w.pronunciation && (
                  <div className="text-xs mb-2" style={{ color: 'var(--color-text-dim)' }}>{w.pronunciation}</div>
                )}
                {w.meanings.map((m, i) => (
                  <div key={i} className="mb-3">
                    <div className="text-xs font-semibold" style={{ color: 'var(--color-text-dim)' }}>
                      {m.order}. [{m.part_of_speech}] {m.korean}
                    </div>
                    {m.tested_synonyms?.length > 0 && (
                      <div className="text-sm mt-0.5" style={{ color: 'var(--color-primary)' }}>
                        {m.tested_synonyms.join(', ')}
                      </div>
                    )}
                    {m.important_synonyms?.length > 0 && (
                      <div className="text-xs mt-0.5" style={{ color: 'var(--color-info)' }}>
                        {m.important_synonyms.join(', ')}
                      </div>
                    )}
                    {m.example_en && (
                      <div className="text-xs mt-1 italic" style={{ color: 'var(--color-text-dim)' }}>{m.example_en}</div>
                    )}
                    {m.example_ko && (
                      <div className="text-xs" style={{ color: 'var(--color-text-dim)' }}>{m.example_ko}</div>
                    )}
                  </div>
                ))}
                {w.exam_tip && (
                  <div className="p-2 rounded-lg text-xs mt-2" style={{ background: 'var(--color-surface-light)', color: 'var(--color-warning)' }}>
                    {w.exam_tip}
                  </div>
                )}
                {w.derivatives?.length > 0 && (
                  <div className="text-xs mt-2" style={{ color: 'var(--color-text-dim)' }}>
                    Derivatives: {w.derivatives.map(d => `${d.pos} ${d.word}`).join(', ')}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function Chip({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 rounded-full text-xs whitespace-nowrap border-none cursor-pointer transition-colors"
      style={{
        background: active ? 'var(--color-primary)' : 'var(--color-surface-light)',
        color: active ? '#fff' : 'var(--color-text-dim)',
      }}
    >
      {label}
    </button>
  );
}
