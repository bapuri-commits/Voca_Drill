# Voca_Drill — 아키텍처

## 개요

공인영어시험(TOEFL/TOEIC) 단어 학습 프로그램.
CLI로 시작하여 SyOps 웹 서비스로 확장하는 경로를 밟는다.

## 해결하는 문제

1. **체계적인 단어 학습 부재** — 단어장을 보기만 하면 암기 효율이 낮음. 능동적 반복 학습(drill) 필요
2. **학습 진도 추적 불가** — 어떤 단어를 잘 알고, 어떤 단어가 약한지 데이터로 관리되지 않음
3. **시험별 빈출 단어 우선순위** — TOEFL/TOEIC 각각의 빈출 단어를 구분하여 집중 학습

## Phase별 아키텍처

### Phase 1: CLI Tool

```
┌─────────────────────────────────────┐
│  CLI (Typer)                        │
│  ├── drill      (퀴즈/반복 학습)     │
│  ├── review     (오답/약점 복습)     │
│  ├── stats      (학습 통계)          │
│  ├── import     (단어장 가져오기)     │
│  └── export     (학습 결과 내보내기)  │
├─────────────────────────────────────┤
│  Core Services                      │
│  ├── WordBank      (단어 DB 관리)    │
│  ├── DrillEngine   (학습 세션 로직)   │
│  ├── Scheduler     (간격 반복 스케줄) │
│  ├── StatsTracker  (학습 통계)       │
│  └── LLMService    (예문/힌트 생성)   │
├─────────────────────────────────────┤
│  Data Layer                         │
│  ├── SQLite (학습 이력, 단어 DB)     │
│  └── wordlists/ (TOEFL, TOEIC 원본) │
└─────────────────────────────────────┘
```

### Phase 2: SyOps 웹 서비스

```
┌──────────────┐   API    ┌──────────────┐
│  SyOps Web   │ ◄──────► │  Voca_Drill  │
│  (React UI)  │          │  (FastAPI)   │
└──────────────┘          └──────────────┘
```

Phase 1의 Core Services를 FastAPI로 래핑하여 SyOps에 배포한다.

## 레이어 구조

```
voca_drill/
├── cli.py              # CLI 진입점 (Typer)
├── config.py           # 설정 로드
├── services/
│   ├── wordbank.py     # WordBank — 단어 DB CRUD
│   ├── drill.py        # DrillEngine — 퀴즈/학습 세션
│   ├── scheduler.py    # Scheduler — 간격 반복 (SM-2 등)
│   ├── stats.py        # StatsTracker — 학습 통계
│   └── llm.py          # LLMService — 예문/힌트 생성
├── data/
│   ├── models.py       # SQLAlchemy 모델
│   └── database.py     # DB 연결/세션 관리
└── api.py              # Phase 2: FastAPI 서버
```

### 레이어 규칙

- **CLI** → Services만 호출. Data 레이어 직접 접근 금지.
- **Services** → Data 레이어를 통해 DB 접근. 직접 SQL 금지.
- **Data** → SQLAlchemy ORM으로 DB 접근 캡슐화.

## 핵심 학습 알고리즘

### 간격 반복 (Spaced Repetition)

SM-2 알고리즘 기반. 각 단어의 숙련도에 따라 복습 간격을 조절한다.

- **새 단어**: 바로 다음 세션에서 복습
- **정답 연속**: 간격 점차 확대 (1일 → 3일 → 7일 → 14일 → 30일)
- **오답 시**: 간격 리셋, 다음 세션에서 재출제

### 학습 세션 구성

- **퀴즈 모드**: 영→한, 한→영, 예문 빈칸 채우기
- **오답 복습**: 틀린 단어 집중 반복
- **Daily Goal**: 일일 목표 단어 수 설정

## 기술 스택

| 구분 | 선택 | 이유 |
|------|------|------|
| 언어 | Python 3.12 | 기존 프로젝트와 통일 |
| CLI | Typer | 기존 패턴 (ObsidianPilot) |
| DB | SQLAlchemy + SQLite | 로컬 학습 이력, 경량 |
| LLM | Anthropic Claude API | 예문 생성, 힌트 |
| 웹 (Phase 2) | FastAPI | SyOps 배포 |
| UI (Phase 2) | React (SyOps 내) | 기존 SyOps 스택 |

## 의존 관계

```
Voca_Drill
├── deploys to → SyOps (Phase 2)
├── pattern reference → Algorithm_Drill (drill 컨셉)
└── pattern reference → ObsidianPilot (CLI→서비스 경로)
```
