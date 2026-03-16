"""FastAPI 엔드포인트 통합 테스트."""

import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = "http://localhost:8400"


def get(path):
    r = urllib.request.urlopen(f"{BASE}{path}")
    return json.loads(r.read())


def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=body, headers={"Content-Type": "application/json"}
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())


passed = 0

# 1. words list
words = get("/api/words?limit=2")
assert len(words) == 2, f"expected 2, got {len(words)}"
assert words[0]["english"] == "exploit"
print(f"[OK] 1. GET /api/words - {len(words)} words")
passed += 1

# 2. chapters
ch = get("/api/words/chapters")
assert len(ch) >= 5, f"expected >=5 chapters, got {len(ch)}"
print(f"[OK] 2. GET /api/words/chapters - {len(ch)} chapters")
passed += 1

# 3. word detail
w = get("/api/words/1")
assert w["english"] == "exploit"
assert w["frequency"] == 3
assert len(w["meanings"]) >= 1
assert len(w["meanings"][0]["tested_synonyms"]) >= 1
print(f"[OK] 3. GET /api/words/1 - {w['english']}, {len(w['meanings'])} meanings")
passed += 1

# 4. daily stats
d = get("/api/stats/daily")
assert "words_studied" in d
print(f"[OK] 4. GET /api/stats/daily - words_studied={d['words_studied']}")
passed += 1

# 5. overall progress
o = get("/api/stats/overall")
assert o["total_words"] == 282
print(f"[OK] 5. GET /api/stats/overall - total={o['total_words']}")
passed += 1

# 6. streak
s = get("/api/stats/streak")
assert "streak_days" in s
print(f"[OK] 6. GET /api/stats/streak - {s['streak_days']} days")
passed += 1

# 7. book tests list
t = get("/api/book-tests")
assert len(t) >= 5
print(f"[OK] 7. GET /api/book-tests - {len(t)} tests")
passed += 1

# 8. book test detail
if t:
    td = get(f"/api/book-tests/{t[0]['id']}")
    assert "questions" in td
    print(f"[OK] 8. GET /api/book-tests/{t[0]['id']} - {len(td['questions'])} questions")
    passed += 1
else:
    print("[SKIP] 8. no book tests")

# 9. create session
sess = post("/api/sessions", {"size": 5})
sid = sess["session_id"]
assert sess["total"] >= 1
print(f"[OK] 9. POST /api/sessions - id={sid[:8]}..., total={sess['total']}")
passed += 1

# 10. next word
nw = get(f"/api/sessions/{sid}/next")
assert nw["complete"] is False
assert "quiz" in nw
quiz = nw["quiz"]
print(f"[OK] 10. GET next - type={quiz['quiz_type']}, word_id={quiz['word_id']}")
passed += 1

# 11. answer
ans = post(f"/api/sessions/{sid}/answer", {
    "word_id": quiz["word_id"],
    "quality": 2,
    "quiz_type": quiz["quiz_type"],
})
assert "combo" in ans
print(f"[OK] 11. POST answer - combo={ans['combo']}, level={ans['review']['mastery_level']}")
passed += 1

# 12. finish session
fin = post(f"/api/sessions/{sid}/finish", {})
assert "total_words" in fin
print(f"[OK] 12. POST finish - total={fin['total_words']}, correct={fin['correct_count']}")
passed += 1

# 13. quiz generate
q = get("/api/quiz/1")
assert q["correct_answer"] == "exploit"
print(f"[OK] 13. GET /api/quiz/1 - type={q['quiz_type']}")
passed += 1

# 14. typing check
tc = post("/api/quiz/typing/check", {"correct": "exploit", "user_input": "exploet"})
assert tc["is_close"] is True
print(f"[OK] 14. POST typing/check - close={tc['is_close']}, dist={tc['distance']}")
passed += 1

print(f"\n=== {passed}/14 TESTS PASSED ===")
