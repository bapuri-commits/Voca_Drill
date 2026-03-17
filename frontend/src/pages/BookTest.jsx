import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

const TYPE_LABELS = {
  quiz: 'Day Quiz',
  review_test: 'Review TEST',
  final_test: 'Final TEST',
};

const TYPE_ORDER = ['quiz', 'review_test', 'final_test'];

export default function BookTest() {
  const nav = useNavigate();
  const [view, setView] = useState('list');
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testData, setTestData] = useState(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [revealed, setRevealed] = useState(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    api.getBookTests()
      .then(setTests)
      .catch(() => {})
      .finally(() => setLoading(false));
    return () => { if (timeoutRef.current) clearTimeout(timeoutRef.current); };
  }, []);

  const startTest = async (testId) => {
    setLoading(true);
    try {
      const data = await api.getBookTest(testId);
      setTestData(data);
      setCurrentIdx(0);
      setAnswers({});
      setRevealed(false);
      setView('taking');
    } catch {}
    setLoading(false);
  };

  const selectAnswer = (questionId, choice) => {
    if (revealed || answers[questionId]) return;
    setAnswers(prev => ({ ...prev, [questionId]: choice }));
    setRevealed(true);

    timeoutRef.current = setTimeout(() => {
      setRevealed(false);
      if (currentIdx < testData.questions.length - 1) {
        setCurrentIdx(i => i + 1);
      } else {
        setView('results');
      }
    }, 1000);
  };

  if (loading) {
    return (
      <div className="max-w-md mx-auto p-4">
        <div className="flex items-center gap-3 mb-6">
          <BackButton onClick={() => nav('/study')} />
          <h1 className="text-xl font-bold">Book Test</h1>
        </div>
        <Spinner />
      </div>
    );
  }

  if (view === 'results' && testData) {
    const questions = testData.questions;
    let correct = 0;
    questions.forEach(q => {
      if (answers[q.id] === q.answer) correct++;
    });
    const rate = Math.round((correct / questions.length) * 100);

    return (
      <div className="max-w-md mx-auto p-4">
        <div className="flex items-center gap-3 mb-6">
          <BackButton onClick={() => setView('list')} />
          <h1 className="text-xl font-bold">Results</h1>
        </div>

        <div className="rounded-2xl p-6 mb-6 text-center" style={{ background: 'var(--color-surface)' }}>
          <div className="text-4xl mb-2">
            {rate >= 80 ? '🎉' : rate >= 50 ? '💪' : '📚'}
          </div>
          <div className="text-3xl font-bold mb-1">{rate}%</div>
          <div className="text-sm" style={{ color: 'var(--color-text-dim)' }}>
            {correct} / {questions.length} correct
          </div>
          <div className="text-xs mt-1" style={{ color: 'var(--color-text-dim)' }}>
            {testData.test_name}
          </div>
        </div>

        <div className="flex flex-col gap-2 mb-6">
          {questions.map((q, i) => {
            const userAnswer = answers[q.id];
            const isCorrect = userAnswer === q.answer;
            const choices = parseChoices(q.choices);

            return (
              <div key={q.id} className="rounded-xl p-3" style={{ background: 'var(--color-surface)' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm">{isCorrect ? '✅' : '❌'}</span>
                  <span className="text-sm font-bold">
                    {i + 1}. {q.target_word || q.question_text}
                  </span>
                </div>
                {!isCorrect && (
                  <div className="text-xs ml-6" style={{ color: 'var(--color-text-dim)' }}>
                    Your: {userAnswer} → Correct: {q.answer}
                    {choices[q.answer] && ` (${choices[q.answer]})`}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => {
              setCurrentIdx(0);
              setAnswers({});
              setRevealed(false);
              setView('taking');
            }}
            className="flex-1 py-3 rounded-xl border-none cursor-pointer font-bold text-white transition-transform active:scale-95"
            style={{ background: 'var(--color-primary)' }}
          >
            Retry
          </button>
          <button
            onClick={() => setView('list')}
            className="flex-1 py-3 rounded-xl border-none cursor-pointer font-bold transition-transform active:scale-95"
            style={{ background: 'var(--color-surface)', color: 'var(--color-text)' }}
          >
            Back to List
          </button>
        </div>
      </div>
    );
  }

  if (view === 'taking' && testData) {
    const question = testData.questions[currentIdx];
    const choices = parseChoices(question.choices);
    const choiceKeys = Object.keys(choices).sort();
    const total = testData.questions.length;
    const userAnswer = answers[question.id];

    return (
      <div className="fixed inset-0 flex flex-col" style={{ background: 'var(--color-bg)' }}>
        <div className="px-4 pt-3 pb-2 flex-shrink-0">
          <div className="flex justify-between text-xs mb-1.5" style={{ color: 'var(--color-text-dim)' }}>
            <span>{currentIdx + 1} / {total}</span>
            <span>{testData.test_name}</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-light)' }}>
            <div
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{ width: `${(currentIdx / total) * 100}%`, background: 'var(--color-primary)' }}
            />
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center px-4 py-2 overflow-hidden">
          <div className="w-full max-w-sm">
            <div className="rounded-2xl p-6 mb-6 text-center" style={{ background: 'var(--color-surface)' }}>
              {question.question_text && (
                <div className="text-sm mb-2" style={{ color: 'var(--color-text-dim)' }}>
                  {question.question_text}
                </div>
              )}
              <div className="text-2xl font-bold">{question.target_word}</div>
            </div>

            <div className="flex flex-col gap-3">
              {choiceKeys.map(key => {
                const text = choices[key];
                const isCorrectChoice = key === question.answer;
                const isSelected = userAnswer === key;

                let style = {
                  background: 'var(--color-surface)',
                  borderColor: 'var(--color-surface-light)',
                  color: 'var(--color-text)',
                };

                if (revealed) {
                  if (isCorrectChoice) {
                    style = {
                      background: 'rgba(34, 197, 94, 0.15)',
                      borderColor: '#22c55e',
                      color: '#22c55e',
                    };
                  } else if (isSelected) {
                    style = {
                      background: 'rgba(239, 68, 68, 0.15)',
                      borderColor: '#ef4444',
                      color: '#ef4444',
                    };
                  } else {
                    style.opacity = 0.4;
                    style.color = 'var(--color-text-dim)';
                  }
                }

                return (
                  <button
                    key={key}
                    onClick={() => selectAnswer(question.id, key)}
                    disabled={revealed}
                    className="w-full py-4 px-5 rounded-xl text-left text-base font-semibold border-2 cursor-pointer transition-all duration-300 active:scale-[0.98] disabled:cursor-default"
                    style={style}
                  >
                    <span className="mr-3 opacity-50 uppercase">{key}.</span>
                    {text}
                    {revealed && isCorrectChoice && (
                      <span className="float-right text-lg">✓</span>
                    )}
                    {revealed && isSelected && !isCorrectChoice && (
                      <span className="float-right text-lg">✗</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <div className="px-4 pb-6 pt-2 flex-shrink-0">
          <div className="text-center text-sm py-3" style={{ color: 'var(--color-surface-light)' }}>
            {revealed
              ? (userAnswer === question.answer ? 'Correct!' : 'Wrong')
              : 'Select the correct answer'}
          </div>
        </div>
      </div>
    );
  }

  const grouped = {};
  tests.forEach(t => {
    if (!grouped[t.test_type]) grouped[t.test_type] = [];
    grouped[t.test_type].push(t);
  });

  return (
    <div className="max-w-md mx-auto p-4">
      <div className="flex items-center gap-3 mb-6">
        <BackButton onClick={() => nav('/study')} />
        <h1 className="text-xl font-bold">Book Test</h1>
      </div>

      {tests.length === 0 ? (
        <div className="rounded-2xl p-8 text-center" style={{ background: 'var(--color-surface)' }}>
          <div className="text-4xl mb-3">📝</div>
          <p className="text-sm" style={{ color: 'var(--color-text-dim)' }}>
            등록된 교재 테스트가 없습니다.
          </p>
        </div>
      ) : (
        TYPE_ORDER.map(type => {
          const list = grouped[type];
          if (!list?.length) return null;
          return (
            <div key={type} className="mb-6">
              <h2 className="text-xs font-semibold uppercase tracking-wider mb-3"
                  style={{ color: 'var(--color-text-dim)' }}>
                {TYPE_LABELS[type] || type}
              </h2>
              <div className="flex flex-col gap-2">
                {list.map(t => (
                  <button
                    key={t.id}
                    onClick={() => startTest(t.id)}
                    className="w-full p-4 rounded-xl border-none cursor-pointer text-left transition-transform active:scale-[0.98]"
                    style={{ background: 'var(--color-surface)' }}
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold">{t.test_name}</span>
                      <span className="text-xs" style={{ color: 'var(--color-text-dim)' }}>
                        {t.question_count}문제
                      </span>
                    </div>
                    {t.covers?.length > 0 && (
                      <div className="text-xs mt-1" style={{ color: 'var(--color-text-dim)' }}>
                        {t.covers.join(', ')}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

function parseChoices(choices) {
  if (!choices) return {};
  if (choices.label && choices.text) {
    return { [choices.label]: choices.text };
  }
  const result = {};
  for (const [k, v] of Object.entries(choices)) {
    if (/^[a-z]$/i.test(k)) {
      result[k.toLowerCase()] = v;
    }
  }
  return result;
}

function BackButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-8 h-8 rounded-full flex items-center justify-center border-none cursor-pointer text-base"
      style={{ background: 'var(--color-surface)', color: 'var(--color-text)' }}
    >
      ←
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
