# Voca_Drill — 기능 명세

## Phase 1: CLI Tool

### 1.1 단어장 관리 (`wordbank`)

TOEFL/TOEIC 단어장을 가져오고 관리한다.

**기능:**

- **가져오기**: CSV/JSON 형식의 단어장 파일을 DB에 등록
  - 필수 필드: 영어 단어, 한국어 뜻
  - 선택 필드: 품사, 예문, 시험 유형(TOEFL/TOEIC), 난이도
- **목록**: 등록된 단어장 목록, 단어 수, 학습 진도 요약
- **태그/그룹**: 단어를 Day별, 주제별로 그룹핑

**CLI 예시:**

```bash
drill wordbank import toefl_words.csv --type toefl
drill wordbank import toeic_words.csv --type toeic
drill wordbank list
drill wordbank stats --type toefl
```

### 1.2 학습 세션 (`drill`)

퀴즈 형태의 반복 학습 세션.

**기능:**

- **퀴즈 시작**: 설정에 따라 학습 세션 시작
  - 모드: 영→한, 한→영, 예문 빈칸 채우기
  - 범위: 전체, 시험별(TOEFL/TOEIC), 그룹별, 오답만, 새 단어만
  - 수량: 세션당 학습할 단어 수 (기본 20)
- **간격 반복**: SM-2 알고리즘으로 복습 대상 자동 선정
- **세션 결과**: 정답률, 소요 시간, 약점 단어 요약

**CLI 예시:**

```bash
drill start                           # 기본 세션 (복습 대상 우선)
drill start --type toefl --count 30   # TOEFL 30개
drill start --mode en2kr              # 영→한 모드
drill start --mode kr2en              # 한→영 모드
drill start --weak-only               # 약점 단어만
drill start --new-only --count 10     # 새 단어 10개
```

### 1.3 복습 (`review`)

오답 및 약점 단어 집중 복습.

**기능:**

- **오답 복습**: 최근 세션에서 틀린 단어 재학습
- **약점 리스트**: 정답률이 낮은 단어 목록
- **마킹**: 특정 단어를 "중요" 또는 "숙지" 표시

**CLI 예시:**

```bash
drill review                          # 오답 복습 세션
drill review --last 3                 # 최근 3세션의 오답
drill weak                            # 약점 단어 목록
drill mark "ubiquitous" --mastered    # 숙지 표시
drill mark "ephemeral" --important    # 중요 표시
```

### 1.4 학습 통계 (`stats`)

학습 진도와 성과를 추적한다.

**기능:**

- **일일 통계**: 오늘 학습한 단어 수, 정답률
- **전체 진도**: 시험별 총 단어 대비 학습/숙지 비율
- **트렌드**: 일별/주별 학습량 변화
- **예상 완료일**: 현재 속도 기준 전체 단어 학습 완료 예상

**CLI 예시:**

```bash
drill stats                           # 전체 통계 요약
drill stats --today                   # 오늘 학습 현황
drill stats --type toefl              # TOEFL 진도
drill stats --trend --days 30         # 30일 트렌드
```

### 1.5 LLM 보조 (`ai`)

LLM을 활용한 학습 보조 기능.

**기능:**

- **예문 생성**: 특정 단어가 포함된 자연스러운 예문 생성
- **어원 설명**: 단어의 어원과 연상 기억법 제공
- **유사어/반의어**: 관련 단어 네트워크 제공
- **문맥 힌트**: 시험 출제 경향에 맞는 힌트

**CLI 예시:**

```bash
drill ai example "ubiquitous"         # 예문 생성
drill ai etymology "ubiquitous"       # 어원 설명
drill ai similar "happy"              # 유사어
```

## Phase 2: SyOps 웹 서비스 (계획)

Phase 1의 Core Services를 FastAPI로 래핑하여 SyOps에 배포.

### 웹 UI 기능

| 기능 | 설명 |
|------|------|
| 학습 대시보드 | 진도, 통계, 캘린더 히트맵 |
| 웹 퀴즈 | 카드 플립, 객관식, 타이핑 |
| 단어장 관리 | 업로드, 편집, 그룹핑 |
| 복습 알림 | 간격 반복 스케줄 기반 알림 |

## 우선순위

1. **Phase 1-1**: 단어 DB + 가져오기 (WordBank, Data Layer)
2. **Phase 1-2**: 퀴즈 엔진 (DrillEngine, 기본 영→한/한→영)
3. **Phase 1-3**: 간격 반복 (Scheduler, SM-2)
4. **Phase 1-4**: 학습 통계 (StatsTracker)
5. **Phase 1-5**: LLM 보조 (예문, 어원)
6. **Phase 2**: FastAPI + SyOps 배포
