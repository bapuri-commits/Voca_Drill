const BASE = '/api';

let _authFetch = null;

export function setAuthFetch(fn) {
  _authFetch = fn;
}

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const fetchFn = _authFetch || fetch;
  const res = await fetchFn(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  getWords: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/words?${qs}`);
  },
  getWord: (id) => request(`/words/${id}`),
  getChapters: () => request('/words/chapters'),

  createSession: (body) => request('/sessions', { method: 'POST', body: JSON.stringify(body) }),
  getNext: (sid, forceQuizType) => {
    const qs = forceQuizType ? `?force_quiz_type=${forceQuizType}` : '';
    return request(`/sessions/${sid}/next${qs}`);
  },
  submitAnswer: (sid, body) => request(`/sessions/${sid}/answer`, { method: 'POST', body: JSON.stringify(body) }),
  finishSession: (sid) => request(`/sessions/${sid}/finish`, { method: 'POST', body: JSON.stringify({}) }),

  getQuiz: (wordId, quizType) => {
    const qs = quizType ? `?quiz_type=${quizType}` : '';
    return request(`/quiz/${wordId}${qs}`);
  },
  checkTyping: (correct, userInput) =>
    request('/quiz/typing/check', { method: 'POST', body: JSON.stringify({ correct, user_input: userInput }) }),

  getDailyStats: (date) => request(`/stats/daily${date ? `?target_date=${date}` : ''}`),
  getOverall: (examType) => request(`/stats/overall${examType ? `?exam_type=${examType}` : ''}`),
  getStreak: () => request('/stats/streak'),

  getBookTests: () => request('/book-tests'),
  getBookTest: (id) => request(`/book-tests/${id}`),

  listPdfs: () => request('/pdf/list'),
};
