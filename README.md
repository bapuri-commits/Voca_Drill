# Voca_Drill

공인영어시험(TOEFL/TOEIC) 단어 학습 프로그램.

## 개요

간격 반복(SM-2) 알고리즘 기반의 영단어 반복 학습 도구. 영→한, 한→영 퀴즈로 능동적으로 단어를 암기하고, 학습 진도와 약점을 데이터로 추적한다.

CLI로 시작하여 SyOps 웹 서비스로 확장 예정.

## 설치

```bash
pip install -r requirements.txt
cp .env.example .env
```

## 사용법

```bash
# 단어장 가져오기
drill wordbank import toefl_words.csv --type toefl

# 학습 세션
drill start                           # 기본 세션
drill start --type toefl --count 30   # TOEFL 30개
drill start --weak-only               # 약점 단어만

# 복습
drill review                          # 오답 복습
drill weak                            # 약점 목록

# 통계
drill stats                           # 전체 통계
drill stats --today                   # 오늘 현황

# LLM 보조
drill ai example "ubiquitous"         # 예문 생성
drill ai etymology "ephemeral"        # 어원 설명
```

## 아키텍처

Phase 1: CLI → Phase 2: SyOps 웹 서비스 (FastAPI)

자세한 내용은 `docs/architecture.md` 참고.

## 관련 프로젝트

- [Algorithm_Drill](../Algorithm_Drill) — 알고리즘 drill (C++)
- [SyOps](../SyOps) — 배포 플랫폼 (Phase 2)
