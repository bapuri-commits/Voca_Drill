import { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api';

const QUALITY_BUTTONS = [
  { quality: 0, label: 'Again', color: '#ef4444', sub: 'No idea' },
  { quality: 1, label: 'Hard', color: '#f97316', sub: 'Barely' },
  { quality: 2, label: 'Good', color: '#22c55e', sub: 'Recalled' },
  { quality: 3, label: 'Easy', color: '#3b82f6', sub: 'Instant' },
];

export default function Study() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const forceQuizType = searchParams.get('quiz') || null;
  const [sessionId, setSessionId] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [remaining, setRemaining] = useState(0);
  const [answered, setAnswered] = useState(0);
  const [combo, setCombo] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const sessionRef = useRef(null);

  const mode = searchParams.get('mode') || 'day';
  const chapter = searchParams.get('chapter') || null;

  const startSession = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setSummary(null);
      const body = {};
      if (mode === 'day' && chapter) {
        body.mode = 'day';
        body.chapter = chapter;
      } else if (mode === 'review') {
        body.mode = 'review';
      } else {
        body.size = 15;
      }
      const sess = await api.createSession(body);
      sessionRef.current = sess.session_id;
      setSessionId(sess.session_id);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }, [mode, chapter]);

  const fetchNext = useCallback(async (sid) => {
    try {
      const data = await api.getNext(sid, forceQuizType);
      if (data.complete) {
        const result = await api.finishSession(sid);
        setSummary(result);
        setQuizData(null);
      } else {
        setQuizData(data.quiz);
        setRemaining(data.remaining);
        setAnswered(data.answered);
        setCombo(data.combo);
      }
      setLoading(false);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }, [forceQuizType]);

  useEffect(() => { startSession(); }, [startSession]);
  useEffect(() => { if (sessionId) fetchNext(sessionId); }, [sessionId, fetchNext]);

  const handleAnswer = async (quality) => {
    const sid = sessionRef.current;
    if (!sid || !quizData || submitting) return;
    setSubmitting(true);
    try {
      const res = await api.submitAnswer(sid, {
        word_id: quizData.word_id,
        quality,
        quiz_type: quizData.quiz_type,
      });
      setCombo(res.combo);
      await fetchNext(sid);
    } catch (e) {
      setError(e.message);
    }
    setSubmitting(false);
  };

  if (error) {
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center p-6" style={{ background: 'var(--color-bg)' }}>
        <div className="text-5xl mb-4">:(</div>
        <p className="text-lg mb-6 text-center" style={{ color: 'var(--color-danger)' }}>{error}</p>
        <button onClick={() => nav('/study')} className="px-8 py-3 rounded-xl border-none cursor-pointer font-bold"
                style={{ background: 'var(--color-surface-light)', color: 'var(--color-text)' }}>
          Back
        </button>
      </div>
    );
  }

  if (summary) {
    const rate = summary.total_words ? Math.round((summary.correct_count / summary.total_words) * 100) : 0;
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center p-6" style={{ background: 'var(--color-bg)' }}>
        <div className="text-5xl mb-2">
          {rate >= 80 ? '🎉' : rate >= 50 ? '💪' : '📚'}
        </div>
        <h1 className="text-2xl font-bold mb-1">Session Complete</h1>
        <p className="text-sm mb-6" style={{ color: 'var(--color-text-dim)' }}>{rate}% accuracy</p>

        <div className="w-full max-w-xs rounded-2xl p-5 mb-6" style={{ background: 'var(--color-surface)' }}>
          <div className="grid grid-cols-2 gap-4 text-center">
            <Stat label="Total" value={summary.total_words} />
            <Stat label="Correct" value={summary.correct_count} />
            <Stat label="New" value={summary.new_words} />
            <Stat label="Review" value={summary.review_words} />
          </div>
          {summary.max_combo > 1 && (
            <div className="mt-4 text-center text-lg font-bold" style={{ color: 'var(--color-warning)' }}>
              Max Combo {summary.max_combo}
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <button onClick={() => { startSession(); }}
                  className="px-8 py-3 rounded-xl border-none cursor-pointer font-bold transition-transform active:scale-95"
                  style={{ background: 'var(--color-primary)', color: '#fff' }}>
            Again
          </button>
          <button onClick={() => nav('/study')}
                  className="px-8 py-3 rounded-xl border-none cursor-pointer font-bold transition-transform active:scale-95"
                  style={{ background: 'var(--color-surface-light)', color: 'var(--color-text)' }}>
            Home
          </button>
        </div>
      </div>
    );
  }

  if (loading || !quizData) {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: 'var(--color-bg)' }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-3 border-t-transparent animate-spin"
               style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent' }} />
          <span className="text-sm" style={{ color: 'var(--color-text-dim)' }}>Loading...</span>
        </div>
      </div>
    );
  }

  const total = answered + remaining;

  return (
    <div className="fixed inset-0 flex flex-col" style={{ background: 'var(--color-bg)' }}>
      {/* Progress Bar */}
      <div className="px-4 pt-3 pb-2 flex-shrink-0">
        <div className="flex justify-between text-xs mb-1.5" style={{ color: 'var(--color-text-dim)' }}>
          <span>{answered + 1} / {total}</span>
          {combo > 0 && (
            <span className="font-bold" style={{ color: 'var(--color-warning)' }}>
              Combo {combo}
            </span>
          )}
        </div>
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-light)' }}>
          <div className="h-full rounded-full transition-all duration-500 ease-out"
               style={{ width: `${(answered / total) * 100}%`, background: 'var(--color-primary)' }} />
        </div>
      </div>

      {/* Quiz Area — dispatch by quiz_type */}
      {quizData.quiz_type === 'typing' ? (
        <TypingQuiz
          quizData={quizData}
          onAnswer={handleAnswer}
          submitting={submitting}
        />
      ) : quizData.quiz_type === 'multiple_choice' || quizData.quiz_type === 'reverse' ? (
        <MultipleChoiceQuiz
          quizData={quizData}
          onAnswer={handleAnswer}
          submitting={submitting}
        />
      ) : (
        <CardFlipQuiz
          quizData={quizData}
          onAnswer={handleAnswer}
          submitting={submitting}
        />
      )}
    </div>
  );
}


function CardFlipQuiz({ quizData, onAnswer, submitting }) {
  const [flipped, setFlipped] = useState(false);

  useEffect(() => { setFlipped(false); }, [quizData]);

  const q = quizData.question;
  const front = q.front || {};
  const back = q.back || {};
  const meanings = back.meanings || [];

  return (
    <>
      <div className="flex-1 flex items-center justify-center px-4 py-2 overflow-hidden"
           onClick={() => !flipped && setFlipped(true)}>
        <div className="w-full max-w-sm">
          <div className="relative w-full min-h-[340px]"
               style={{ transformStyle: 'preserve-3d', transition: 'transform 0.5s ease',
                        transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}>

            <div className="absolute inset-0 rounded-2xl p-6 flex flex-col items-center justify-center"
                 style={{ background: 'var(--color-surface)', backfaceVisibility: 'hidden' }}>
              <div className="text-4xl font-bold mb-3">{front.english}</div>
              {front.pronunciation && (
                <div className="text-base mb-2" style={{ color: 'var(--color-text-dim)' }}>{front.pronunciation}</div>
              )}
              <div className="text-sm" style={{ color: 'var(--color-text-dim)' }}>{front.part_of_speech}</div>
              <div className="mt-10 text-sm" style={{ color: 'var(--color-surface-light)' }}>Tap to flip</div>
            </div>

            <div className="absolute inset-0 rounded-2xl p-5 overflow-y-auto"
                 style={{ background: 'var(--color-surface)', backfaceVisibility: 'hidden',
                          transform: 'rotateY(180deg)' }}>
              <div className="text-lg font-bold mb-3 text-center" style={{ color: 'var(--color-text-dim)' }}>
                {front.english}
              </div>
              {meanings.map((m, i) => (
                <div key={i} className="mb-3">
                  <div className="flex items-baseline gap-1 mb-0.5">
                    {meanings.length > 1 && (
                      <span className="text-xs font-bold" style={{ color: 'var(--color-text-dim)' }}>{m.order}.</span>
                    )}
                    <span className="text-xs" style={{ color: 'var(--color-text-dim)' }}>[{m.part_of_speech}]</span>
                  </div>
                  {m.tested_synonyms?.length > 0 && (
                    <div className="text-base font-bold mt-0.5" style={{ color: 'var(--color-primary)' }}>
                      {m.tested_synonyms.join(', ')}
                    </div>
                  )}
                  {m.important_synonyms?.length > 0 && (
                    <div className="text-sm mt-0.5" style={{ color: 'var(--color-info)' }}>
                      {m.important_synonyms.join(', ')}
                    </div>
                  )}
                  <div className="text-sm mt-1" style={{ color: 'var(--color-text-dim)' }}>{m.korean}</div>
                  {m.example_en && (
                    <div className="text-xs mt-1.5 italic leading-relaxed" style={{ color: 'var(--color-text-dim)', opacity: 0.7 }}>
                      {m.example_en}
                    </div>
                  )}
                </div>
              ))}
              {back.exam_tip && (
                <div className="mt-2 p-2.5 rounded-lg text-xs leading-relaxed"
                     style={{ background: 'var(--color-surface-light)', color: 'var(--color-warning)' }}>
                  {back.exam_tip}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 pb-6 pt-2 flex-shrink-0">
        {flipped ? (
          <div className="grid grid-cols-4 gap-2">
            {QUALITY_BUTTONS.map(btn => (
              <button
                key={btn.quality}
                onClick={() => onAnswer(btn.quality)}
                disabled={submitting}
                className="py-3.5 rounded-xl border-none cursor-pointer font-bold text-white text-sm transition-all active:scale-95 disabled:opacity-50"
                style={{ background: btn.color }}
              >
                <div>{btn.label}</div>
                <div className="text-[10px] opacity-70 font-normal mt-0.5">{btn.sub}</div>
              </button>
            ))}
          </div>
        ) : (
          <div className="text-center text-sm py-3" style={{ color: 'var(--color-surface-light)' }}>
            Tap the card to see the answer
          </div>
        )}
      </div>
    </>
  );
}


function MultipleChoiceQuiz({ quizData, onAnswer, submitting }) {
  const [selected, setSelected] = useState(null);
  const [revealed, setRevealed] = useState(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    setSelected(null);
    setRevealed(false);
    return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
  }, [quizData]);

  const q = quizData.question;
  const choices = quizData.choices || [];
  const isReverse = quizData.quiz_type === 'reverse';

  const handleSelect = (choice, idx) => {
    if (revealed || submitting) return;
    setSelected(idx);
    setRevealed(true);

    const quality = choice.is_correct ? 2 : 0;

    timeoutRef.current = setTimeout(() => {
      onAnswer(quality);
    }, 1200);
  };

  const getChoiceStyle = (choice, idx) => {
    if (!revealed) {
      return {
        background: 'var(--color-surface)',
        borderColor: 'var(--color-surface-light)',
        color: 'var(--color-text)',
      };
    }
    if (choice.is_correct) {
      return {
        background: 'rgba(34, 197, 94, 0.15)',
        borderColor: '#22c55e',
        color: '#22c55e',
      };
    }
    if (idx === selected) {
      return {
        background: 'rgba(239, 68, 68, 0.15)',
        borderColor: '#ef4444',
        color: '#ef4444',
      };
    }
    return {
      background: 'var(--color-surface)',
      borderColor: 'var(--color-surface-light)',
      color: 'var(--color-text-dim)',
      opacity: 0.4,
    };
  };

  return (
    <>
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-2 overflow-hidden">
        <div className="w-full max-w-sm">
          {/* Prompt area */}
          <div className="rounded-2xl p-6 mb-6 text-center" style={{ background: 'var(--color-surface)' }}>
            {isReverse ? (
              <>
                <div className="text-xs mb-2 uppercase tracking-wider" style={{ color: 'var(--color-text-dim)' }}>
                  {q.prompt_type === 'english_definition' ? 'Definition' : 'Synonyms'}
                </div>
                <div className="text-lg font-semibold leading-relaxed">{q.prompt}</div>
              </>
            ) : (
              <>
                {q.synonyms?.length > 0 && (
                  <div className="text-lg font-bold mb-3" style={{ color: 'var(--color-primary)' }}>
                    {q.synonyms.join(', ')}
                  </div>
                )}
                {q.korean && (
                  <div className="text-base" style={{ color: 'var(--color-text-dim)' }}>{q.korean}</div>
                )}
                <div className="text-xs mt-3 uppercase tracking-wider" style={{ color: 'var(--color-text-dim)', opacity: 0.6 }}>
                  Choose the correct word
                </div>
              </>
            )}
          </div>

          {/* Choices */}
          <div className="flex flex-col gap-3">
            {choices.map((choice, idx) => (
              <button
                key={idx}
                onClick={() => handleSelect(choice, idx)}
                disabled={revealed || submitting}
                className="w-full py-4 px-5 rounded-xl text-left text-base font-semibold border-2 cursor-pointer transition-all duration-300 active:scale-[0.98] disabled:cursor-default"
                style={getChoiceStyle(choice, idx)}
              >
                <span className="mr-3 opacity-50">{String.fromCharCode(65 + idx)}.</span>
                {choice.word}
                {revealed && choice.is_correct && (
                  <span className="float-right text-lg">✓</span>
                )}
                {revealed && idx === selected && !choice.is_correct && (
                  <span className="float-right text-lg">✗</span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="px-4 pb-6 pt-2 flex-shrink-0">
        <div className="text-center text-sm py-3" style={{ color: 'var(--color-surface-light)' }}>
          {revealed
            ? (choices[selected]?.is_correct ? 'Correct!' : 'Wrong — check the answer above')
            : 'Select the correct answer'}
        </div>
      </div>
    </>
  );
}


function TypingQuiz({ quizData, onAnswer, submitting }) {
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);
  const [checking, setChecking] = useState(false);
  const inputRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    setInput('');
    setResult(null);
    setChecking(false);
    const focusTimer = setTimeout(() => inputRef.current?.focus(), 100);
    return () => {
      clearTimeout(focusTimer);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [quizData]);

  const q = quizData.question;
  const correctAnswer = quizData.correct_answer;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || checking || result) return;

    setChecking(true);
    try {
      const res = await api.checkTyping(correctAnswer, input.trim());
      setResult(res);

      const quality = res.is_correct ? (res.is_close ? 1 : 2) : 0;

      timeoutRef.current = setTimeout(() => {
        onAnswer(quality);
      }, 1500);
    } catch {
      setChecking(false);
    }
  };

  return (
    <>
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-2 overflow-hidden">
        <div className="w-full max-w-sm">
          <div className="rounded-2xl p-6 mb-6 text-center" style={{ background: 'var(--color-surface)' }}>
            <div className="text-xs mb-3 uppercase tracking-wider" style={{ color: 'var(--color-text-dim)' }}>
              Type the word
            </div>
            {q.synonyms?.length > 0 && (
              <div className="text-lg font-bold mb-2" style={{ color: 'var(--color-primary)' }}>
                {q.synonyms.join(', ')}
              </div>
            )}
            {q.korean && (
              <div className="text-base mb-2" style={{ color: 'var(--color-text-dim)' }}>
                {q.korean}
              </div>
            )}
            {q.part_of_speech && (
              <div className="text-xs" style={{ color: 'var(--color-text-dim)', opacity: 0.6 }}>
                {q.part_of_speech} · {q.hint_length} letters
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              disabled={!!result || submitting}
              placeholder="Enter the word..."
              autoComplete="off"
              autoCapitalize="off"
              spellCheck="false"
              className="w-full px-5 py-4 rounded-xl text-lg text-center font-semibold outline-none transition-all border-2"
              style={{
                background: 'var(--color-surface)',
                color: 'var(--color-text)',
                borderColor: result
                  ? result.is_correct ? '#22c55e' : '#ef4444'
                  : 'transparent',
              }}
            />

            {!result && (
              <button
                type="submit"
                disabled={!input.trim() || checking || submitting}
                className="w-full mt-3 py-3.5 rounded-xl border-none cursor-pointer font-bold text-white transition-all active:scale-95 disabled:opacity-40"
                style={{ background: 'var(--color-primary)' }}
              >
                {checking ? 'Checking...' : 'Check'}
              </button>
            )}
          </form>

          {result && (
            <div className="mt-4 rounded-xl p-4 text-center" style={{
              background: result.is_correct ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            }}>
              {result.is_correct ? (
                <>
                  <div className="text-2xl mb-1">{result.is_close ? '🤏' : '✅'}</div>
                  <div className="font-bold" style={{ color: '#22c55e' }}>
                    {result.is_close ? 'Close enough!' : 'Correct!'}
                  </div>
                  {result.is_close && (
                    <div className="text-sm mt-1" style={{ color: 'var(--color-text-dim)' }}>
                      Exact: <strong>{result.correct_answer}</strong>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="text-2xl mb-1">❌</div>
                  <div className="font-bold" style={{ color: '#ef4444' }}>Wrong</div>
                  <div className="text-sm mt-1" style={{ color: 'var(--color-text-dim)' }}>
                    Answer: <strong>{result.correct_answer}</strong>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="px-4 pb-6 pt-2 flex-shrink-0">
        <div className="text-center text-sm py-3" style={{ color: 'var(--color-surface-light)' }}>
          {result
            ? (result.is_correct ? 'Moving on...' : `The answer was "${result.correct_answer}"`)
            : 'Type the English word and press Check'}
        </div>
      </div>
    </>
  );
}


function Stat({ label, value }) {
  return (
    <div>
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-xs mt-0.5" style={{ color: 'var(--color-text-dim)' }}>{label}</div>
    </div>
  );
}
