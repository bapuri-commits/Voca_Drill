# Voca_Drill — 아키텍처

## 개요

공인영어시험(TOEFL/TOEIC) 단어 학습 프로그램.
학습자의 인지 특성(ADHD 경향성)을 고려한 과학적 복습 체계(SM-2 + 라이트너)와 다차원 인출 퀴즈를 결합한다.
1차 데이터는 토플 '초록이' 교재. 단어장 추가로 확장 가능.

## 해결하는 문제

1. **체계적인 단어 학습 부재** — 단어장을 보기만 하면 암기 효율이 낮음. 능동적 반복 학습 + 다차원 인출 연습 필요
2. **학습 진도 추적 불가** — 어떤 단어를 잘 알고, 어떤 단어가 약한지 데이터로 관리되지 않음
3. **복습 타이밍 관리 불가** — 에빙하우스 망각 곡선에 따른 최적 복습 시점을 수동으로 관리할 수 없음
4. **동기 유지 어려움** — ADHD 경향이 있는 학습자에게는 짧고 보상이 명확한 세션이 필요

## 레이어 구조

```
voca_drill/
├── cli.py              # CLI 진입점 (Typer) — import/관리용
├── config.py           # 설정 로드
├── services/
│   ├── wordbank.py     # WordBank — 단어 DB CRUD, import
│   ├── drill.py        # DrillEngine — 세션 구성, 퀴즈 생성
│   ├── scheduler.py    # Scheduler — SM-2 간격 반복
│   ├── stats.py        # StatsTracker — 학습 통계
│   └── llm.py          # LLMService — 예문/어원 생성 (Phase 3)
├── data/
│   ├── models.py       # SQLAlchemy 모델
│   └── database.py     # DB 연결/세션 관리
└── api.py              # Phase 2: FastAPI 서버
```

### 레이어 규칙

- **CLI** → Services만 호출. Data 레이어 직접 접근 금지.
- **Services** → Data 레이어를 통해 DB 접근. 직접 SQL 금지.
- **Data** → SQLAlchemy ORM으로 DB 접근 캡슐화.
- **API** → Services를 HTTP로 노출. 비즈니스 로직은 Services에 유지.

## DB 스키마 (초안 — 데이터 확보 후 확정)

> **주의**: 아래 스키마는 초록이 교재 페이지 분석에 기반한 초안이다.
> OCR + NotebookLM 실데이터를 확보한 후에 필드, 관계, 예외 케이스를 파악하여 확정한다.

### 핵심 구조: Word + WordMeaning 분리

초록이는 한 단어가 여러 뜻을 가지며, **뜻마다 다른 영어 동의어 세트와 예문**이 붙는다.
이를 정확히 표현하려면 Word(단어 단위)와 WordMeaning(뜻 단위)을 분리해야 한다.

### Word (단어)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | 자동 증가 |
| english | String, index | 영어 단어 |
| pronunciation | String | 발음 기호 |
| importance | Integer | 중요도/빈출도 (★ 개수, 0-3) |
| derivatives_json | String | 파생어 목록 (JSON array) |
| exam_type | String | 시험 유형 (toefl/toeic) |
| chapter | String | 교재 챕터 (Day 1, Day 2...) |
| word_order | Integer | 교재 내 순서 |
| exam_tip | String | 최신출제 포인트 (nullable) |
| source | String | 데이터 출처 (ocr/notebooklm/manual) |
| created_at | DateTime | 생성일 |

### WordMeaning (뜻 — Word와 1:N)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | 자동 증가 |
| word_id | Integer FK | Word 참조 |
| meaning_order | Integer | 뜻 순서 (1, 2, 3...) |
| part_of_speech | String | 품사 (adj, noun, verb 등) |
| korean | String | 한국어 뜻 (보조) |
| synonyms_json | String | **영어 동의어 목록 (JSON array) — 핵심 학습 대상** |
| example | String | 예문 |
| english_definition | String | 영영 풀이 (NotebookLM 보강, nullable) |

### WordProgress (단어별 학습 진도)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | 자동 증가 |
| word_id | Integer FK, unique | Word 참조 |
| ease_factor | Float | SM-2 ease factor (기본 2.5) |
| interval_days | Integer | 현재 복습 간격 (일) |
| repetitions | Integer | 연속 정답 횟수 |
| next_review | DateTime | 다음 복습 예정일 |
| mastery_level | Integer | 라이트너 단계 (1-5, interval에서 파생) |
| quiz_level | Integer | 해금된 퀴즈 단계 (1-4) |
| total_attempts | Integer | 총 시도 횟수 |
| correct_count | Integer | 총 정답 횟수 |
| status | String | new/learning/review/familiar/mastered |
| updated_at | DateTime | 최종 갱신일 |

### LearningRecord (개별 응답 이력)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | 자동 증가 |
| word_id | Integer FK | Word 참조 |
| session_id | String FK | LearningSession 참조 |
| quiz_type | String | card_flip / multiple_choice / reverse / typing |
| quality | Integer | 평가 등급 (0: 모름, 1: 헷갈림, 2: 알겠음, 3: 완벽) |
| is_correct | Integer | 정답 여부 (객관식/타이핑 퀴즈용) |
| response_time_ms | Integer | 응답 시간 (ms) |
| answered_at | DateTime | 응답 시각 |

### LearningSession (학습 세션)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | String PK | UUID |
| started_at | DateTime | 시작 시각 |
| ended_at | DateTime | 종료 시각 (null이면 진행중) |
| total_words | Integer | 세션 내 총 단어 수 |
| correct_count | Integer | 정답 수 |
| new_words_count | Integer | 새 단어 수 |
| review_words_count | Integer | 복습 단어 수 |
| max_combo | Integer | 최대 콤보 |
| status | String | in_progress / completed / abandoned |

### DailyStats (일일 통계 캐시)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer PK | 자동 증가 |
| date | Date, unique | 날짜 |
| words_studied | Integer | 학습한 단어 수 |
| new_words | Integer | 새로 학습한 단어 수 |
| review_words | Integer | 복습한 단어 수 |
| correct_rate | Float | 정답률 |
| sessions_count | Integer | 세션 수 |
| streak_days | Integer | 연속 학습 일수 |
| study_time_sec | Integer | 총 학습 시간 (초) |

## 핵심 학습 알고리즘

### SM-2 간격 반복

에빙하우스 망각 곡선 기반. 각 단어의 ease_factor에 따라 복습 간격을 동적 계산.

**간격 계산:**
- 첫 정답: interval = 1일
- 두 번째 정답: interval = 3일
- 이후: interval = 이전 interval × ease_factor

**ease_factor 갱신:**
- `EF' = EF + (0.1 - (3 - quality) × (0.08 + (3 - quality) × 0.02))`
- 최솟값: 1.3

**오답('모름') 시:**
- interval 리셋 (1일), repetitions 리셋 (0)
- ease_factor는 유지하되 하한 체크

### 퀴즈 유형 연동

mastery_level이 오르면 더 어려운 퀴즈가 해금.
**영어 동의어 중심 학습을 반영:**

| mastery_level | 퀴즈 유형 | 설명 |
|---------------|-----------|------|
| 1-2 | 카드 플립 | 영어 단어 → 영어 동의어 + 한국어 뜻, 자기 평가 |
| 3 | 객관식 | 영어 동의어 보고 원래 단어 선택 (토플 대비) |
| 4 | 역방향 | 영영 풀이 → 영어 단어 맞히기 |
| 5 | 타이핑 | 동의어/뜻 보고 영어 단어 직접 입력 |

## 데이터 파이프라인

```
초록이 교재
    ↓ OCR 스캔
원본 텍스트
    ↓ 정제 (단어/뜻/품사/동의어 분리)
    ↓ NotebookLM 분석 → 영영 풀이, 추가 예문, 유의어/반의어 그룹
    ↓ JSON 파일로 병합
    ↓ CLI import (초록이용 파서)
    DB
```

다른 단어장 추가 시: 해당 단어장용 파서만 추가. 최소 필드(english, korean)만 있으면 import 가능.

## 기술 스택

| 구분 | 선택 | 이유 |
|------|------|------|
| 언어 | Python 3.12 | 기존 프로젝트와 통일 |
| CLI | Typer | import/관리용 |
| DB | SQLAlchemy + SQLite | 경량, Phase 2에서도 그대로 유지 |
| 웹 API | FastAPI | Phase 2 |
| 프론트엔드 | React (SyOps 내) | 기존 SyOps 스택, 모바일 퍼스트 |
| LLM | Anthropic Claude API | 예문/어원 생성 (Phase 3) |

## Phase별 아키텍처

### Phase 1: 서비스 레이어

```
CLI (import/관리)
 └─→ Services (핵심 로직)
      └─→ Data (SQLAlchemy + SQLite)
```

### Phase 2: 웹 서비스

```
┌──────────────┐   API    ┌──────────────┐
│  SyOps Web   │ ◄──────► │  Voca_Drill  │
│  (React UI)  │          │  (FastAPI)   │
└──────────────┘          └──────────────┘
```

Phase 1의 Services를 FastAPI로 래핑. React에서 모바일 퍼스트 카드 UI 구현.

## 의존 관계

```
Voca_Drill
├── deploys to → SyOps (Phase 2+)
├── auth shared with → SyOps (JWT_SECRET)
└── data from → 초록이 OCR + NotebookLM (1차), 추후 다른 단어장
```
