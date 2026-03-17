const BASE = '/api';
const TOKEN_KEY = 'voca_token';

async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      window.location.reload();
      throw new Error('Session expired');
    }
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

  getChapterProgress: () => request('/chapters/progress'),
  getReviewCount: () => request('/study/review-count'),

  getBookTests: () => request('/book-tests'),
  getBookTest: (id) => request(`/book-tests/${id}`),

  listBackups: () => request('/backup/list'),
  createBackup: () => request('/backup/create', { method: 'POST' }),
  restoreBackup: (filename) => request(`/backup/restore/${filename}`, { method: 'POST' }),
  deleteBackup: (filename) => request(`/backup/${filename}`, { method: 'DELETE' }),

  listPdfs: () => request('/pdf/list'),
};
