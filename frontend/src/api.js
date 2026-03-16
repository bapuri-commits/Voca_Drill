const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
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
  // Words
  getWords: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/words?${qs}`);
  },
  getWord: (id) => request(`/words/${id}`),
  getChapters: () => request('/words/chapters'),

  // Sessions
  createSession: (body) => request('/sessions', { method: 'POST', body: JSON.stringify(body) }),
  getNext: (sid) => request(`/sessions/${sid}/next`),
  submitAnswer: (sid, body) => request(`/sessions/${sid}/answer`, { method: 'POST', body: JSON.stringify(body) }),
  finishSession: (sid) => request(`/sessions/${sid}/finish`, { method: 'POST', body: JSON.stringify({}) }),

  // Quiz
  getQuiz: (wordId, quizType) => {
    const qs = quizType ? `?quiz_type=${quizType}` : '';
    return request(`/quiz/${wordId}${qs}`);
  },
  checkTyping: (correct, userInput) =>
    request('/quiz/typing/check', { method: 'POST', body: JSON.stringify({ correct, user_input: userInput }) }),

  // Stats
  getDailyStats: (date) => request(`/stats/daily${date ? `?target_date=${date}` : ''}`),
  getOverall: (examType) => request(`/stats/overall${examType ? `?exam_type=${examType}` : ''}`),
  getStreak: () => request('/stats/streak'),

  // Book Tests
  getBookTests: () => request('/book-tests'),
  getBookTest: (id) => request(`/book-tests/${id}`),
};
