# Voca_Drill — 데이터 추출 가이드

## 목적

초록이(해커스 토플 보카) PDF에서 단어 데이터를 추출하여 DB에 넣을 JSON을 만드는 것.
교재의 학습 설계를 분석하는 것이 아니라, **정해진 스키마에 맞는 단어 데이터를 정확하게 뽑아내는 것**이 목표.

## 전제 조건

- 초록이 PDF 확보 완료 (스캔본, ~200MB)
- **30 Days × ~56단어 ≈ 1,680단어**
- 각 Day = 10페이지 (단어 9페이지 + Quiz 1페이지)
- 이 프로그램은 자체 학습 엔진(SM-2 + 라이트너)이 있으므로 교재의 복습/테스트 구조 분석은 불필요
- 교재의 핵심: **한국어 뜻이 아닌 영어 동의어/유의어로 암기**

## 교재 데이터 구조 (분석 완료)

> 상세 분석: `docs/bookpdf/hackers_voca_analysis.md`

### 단어 6가지 구성 요소

| # | 구성 요소 | 설명 |
|---|----------|------|
| ① | 표제어 | 기출 단어, 출제빈도 ★1~3개, Day 내 빈도순 배치 |
| ② | 기출동의어 | 토플 시험에서 **정답으로 출제된** 동의어 (녹색 강조) |
| ③ | 중요동의어 | 출제 가능성 높은 동의어 (일반 표기) |
| ④ | 기출파생어 | 시험에 출제된 파생어 (품사+단어) |
| ⑤ | 예문 | 토플 경향 반영 예문 + 페이지 하단 한국어 해석 |
| ⑥ | 최신출제 포인트 | 추가 의미, 혼동어, 관련 동의어 팁 (선별적) |

### 기출동의어 vs 중요동의어

이 구분이 학습에 핵심적:
- **기출동의어**: 실제 시험 정답으로 나온 것 → 최우선 암기 대상
- **중요동의어**: 출제 가능성 높음 → 숙련도 오르면 확장 학습

### 다의어 처리

한 단어에 여러 뜻이 있으면 번호를 매겨 각각 동의어 + 예문 제공.
예: account for → ①설명하다 ②차지하다 ③원인이 되다 (각각 별도 동의어 세트)

### 테스트 3종

| 유형 | 위치 | 형식 | 문제 수 |
|------|------|------|--------|
| Quiz | 각 Day 마지막 페이지 | 동의어 매칭 (단어 10개 ↔ 보기 ⓐ~ⓙ) | 10 |
| Review TEST | 5Day마다 (p.68, 120, 172, 224, 276, 328) | 문장 속 밑줄 단어 동의어 4지선다 | 10 |
| Final TEST | p.330~335 (3개) | Review TEST와 유사 추정 | 미확인 |

---

## 추출 대상

### 1. 단어 데이터 (30 Days, ~1,680단어)

메인 데이터. Day별로 추출.

### 2. Quiz 데이터 (30개, Day별 10문제)

각 Day 마지막 페이지의 동의어 매칭 퀴즈.

### 3. Review TEST 데이터 (6개, 5Day마다 10문제)

문장 속 동의어 4지선다 문제. 교재 테스트 모드로 활용.

### 4. Final TEST 데이터 (3개)

최종 테스트. 형식은 추출 시 확인.

### 5. 단어 레이아웃 설명 페이지 (p.8~9)

추출 프롬프트에 참고 자료로 첨부하여 AI의 정확도를 높임.

---

## 파이프라인 (3단계)

```
Step A: 준비              Step B: 추출                  Step C: 검증 + Import
PDF 분할 + 샘플 검증       AI로 JSON 추출                검증 후 DB import

A-1 페이지 맵 확인         B-1 Day별 단어 추출 (30회)     C-1 자동 검증 (스크립트)
A-2 Day 단위 PDF 분할      B-2 Quiz 데이터 추출           C-2 수동 스팟 체크
A-3 Day 01 샘플 추출       B-3 Review/Final TEST 추출     C-3 CLI import
A-4 프롬프트 조정
```

---

## Step A: 준비

### A-1. 페이지 맵 (분석 완료)

> 분석 문서의 "분할 페이지 맵" 참조

| 파일 | Day | 페이지 범위 |
|------|-----|-----------|
| chunk_01 | Day 01 | p.18~27 |
| chunk_02 | Day 02 | p.28~37 |
| chunk_03 | Day 03 | p.38~47 |
| chunk_04 | Day 04 | p.48~57 |
| chunk_05 | Day 05 | p.58~67 |
| chunk_06 | Day 06 | p.70~79 |
| chunk_07 | Day 07 | p.80~89 |
| chunk_08 | Day 08 | p.90~99 |
| chunk_09 | Day 09 | p.100~109 |
| chunk_10 | Day 10 | p.110~119 |
| chunk_11 | Day 11 | p.122~131 |
| chunk_12 | Day 12 | p.132~141 |
| chunk_13 | Day 13 | p.142~151 |
| chunk_14 | Day 14 | p.152~161 |
| chunk_15 | Day 15 | p.162~171 |
| chunk_16 | Day 16 | p.174~183 |
| chunk_17 | Day 17 | p.184~193 |
| chunk_18 | Day 18 | p.194~203 |
| chunk_19 | Day 19 | p.204~213 |
| chunk_20 | Day 20 | p.214~223 |
| chunk_21 | Day 21 | p.226~235 |
| chunk_22 | Day 22 | p.236~245 |
| chunk_23 | Day 23 | p.246~255 |
| chunk_24 | Day 24 | p.256~265 |
| chunk_25 | Day 25 | p.266~275 |
| chunk_26 | Day 26 | p.278~287 |
| chunk_27 | Day 27 | p.288~297 |
| chunk_28 | Day 28 | p.298~307 |
| chunk_29 | Day 29 | p.308~317 |
| chunk_30 | Day 30 | p.318~327 |

테스트 페이지:

| 파일 | 내용 | 페이지 |
|------|------|--------|
| review_test_01-05 | Review TEST Day 1-5 | p.68~69 |
| review_test_06-10 | Review TEST Day 6-10 | p.120~121 |
| review_test_11-15 | Review TEST Day 11-15 | p.172~173 |
| review_test_16-20 | Review TEST Day 16-20 | p.224~225 |
| review_test_21-25 | Review TEST Day 21-25 | p.276~277 |
| review_test_26-30 | Review TEST Day 26-30 | p.328~329 |
| final_tests | Final TEST 1~3 + Answer Key | p.330~337 |

### A-2. Day 단위 PDF 분할

PDF를 Day 단위(10페이지)로 분할. 총 30개 + 테스트 청크.

분할 스크립트로 자동화 가능 (PyPDF2).

### A-3. Day 01 샘플 추출 테스트

전체를 돌리기 전에 **Day 01만 먼저** AI에 넣어서 테스트.

확인할 것:
- OCR 품질 (발음기호 깨짐, 특수문자 오류)
- **기출동의어 vs 중요동의어 구분**이 되는지 (색상 구분이 OCR에서 유지되는지)
- 다의어가 meanings 배열로 정확히 분리되는지
- 예문 + 한국어 해석이 매칭되는지
- 최신출제 포인트가 올바른 단어에 연결되는지
- 단어 수 일치 (Day 01 = 57개)

### A-4. 프롬프트 조정

샘플 결과에 문제가 있으면 프롬프트를 수정.
- 기출/중요동의어 구분이 안 되면 → 레이아웃 설명 페이지에서 색상 규칙 명시
- OCR 오류가 많으면 → 교정 지시 강화

---

## Step B: AI 추출

### 사용할 AI

PDF 직접 입력 가능한 모델:
- **Claude** (PDF 업로드 지원)
- **ChatGPT (GPT-4o)** (PDF 업로드 지원)

### 단어 추출 프롬프트

> **사용법**: 이 프롬프트 + 레이아웃 설명 페이지(p.8~9) + Day 청크 PDF를 함께 AI에 입력

```
이 PDF는 토플 영단어 교재 '해커스 보카(초록이)'의 Day NN 부분입니다.
함께 첨부된 레이아웃 설명 페이지를 참고하여 단어 데이터를 추출해주세요.

## 규칙

1. 한 단어가 여러 뜻을 가지면 meanings 배열에 각각 분리
2. **기출동의어**(tested_synonyms)와 **중요동의어**(important_synonyms)를 구분
   - 기출동의어: 녹색/강조색으로 표시된 동의어 (실제 시험 출제)
   - 중요동의어: 일반 표기된 동의어
   - 구분이 불확실하면 모두 tested_synonyms에 넣고 ocr_note에 기록
3. 한국어 뜻은 교재에 적힌 그대로 (의역하지 말 것)
4. 예문(example_en)은 교재 본문의 영어 예문
5. 예문 해석(example_ko)은 페이지 하단의 한국어 해석
6. 파생어는 {"pos": "n.", "word": "exploitation"} 형태
7. 중요도(frequency)는 ★ 개수 (1~3)
8. 최신출제 포인트(exam_tip)가 있는 단어만 해당 필드 채움, 없으면 null
9. OCR 오류가 의심되면 문맥상 교정하고 ocr_note에 원본과 교정 내용 기록
10. Day 마지막 페이지의 Quiz도 별도로 추출
11. 출력은 JSON만. 설명이나 마크다운 없이 순수 JSON만 출력

## JSON 스키마

{
  "day": "Day 01",
  "words": [
    {
      "word_order": 1,
      "english": "exploit",
      "pronunciation": "[iksplɔ́it]",
      "frequency": 3,
      "derivatives": [{"pos": "n.", "word": "exploitation"}],
      "exam_tip": "exploit는 동사가 아닌 명사로도 많이 쓰인다...",
      "ocr_note": null,
      "meanings": [
        {
          "order": 1,
          "part_of_speech": "v.",
          "korean": "(부당하게) 이용하다",
          "tested_synonyms": ["utilize", "use", "make use of", "take advantage of"],
          "important_synonyms": [],
          "example_en": "Human rights activists have led protests against companies that exploit child labor.",
          "example_ko": "인권 운동가들은 아동의 노동을 이용하는 회사들에 대항하는 시위를 이끌어 왔다."
        }
      ]
    }
  ],
  "quiz": {
    "instruction": "Choose the synonyms.",
    "questions": [
      {
        "number": 1,
        "word": "exploit",
        "choices": {"label": "ⓒ", "text": "utilize, use, make use of"},
        "answer_label": "ⓒ"
      }
    ]
  }
}

PDF의 모든 단어를 빠짐없이 추출해주세요. 예상 단어 수: 56~57개.
```

### Review TEST 추출 프롬프트

```
이 PDF는 토플 영단어 교재 '해커스 보카(초록이)'의 Review TEST 부분입니다.
테스트 문제를 아래 JSON 스키마에 맞춰 추출해주세요.

## 규칙

1. 모든 문제를 빠짐없이 추출
2. 문장 전체(question_text)와 밑줄 단어(highlighted_word)를 구분
3. 보기 4개(A~D)와 정답을 포함
4. 정답은 Answer Key(p.336) 참조 또는 별도 제공
5. 출력은 JSON만

## JSON 스키마

{
  "test_name": "Review TEST Day 1-5",
  "covers": ["Day 01", "Day 02", "Day 03", "Day 04", "Day 05"],
  "questions": [
    {
      "number": 1,
      "question_text": "The travelers replenished their supplies before the journey.",
      "highlighted_word": "replenished",
      "choices": {
        "A": "increased",
        "B": "elevated",
        "C": "refilled",
        "D": "located"
      },
      "answer": "C"
    }
  ]
}
```

### 청크별 반복

30개 Day 청크 + 테스트 청크에 각각 프롬프트 적용. 결과를 별도 JSON으로 저장.

---

## Step C: 검증 + Import

### C-1. 자동 검증

검증 스크립트로 다음을 체크:

- **단어 수**: Day당 56~57개, 총 ~1,680개
- **필수 필드**: english, korean, tested_synonyms 존재 확인
- **빈 동의어 경고**: tested_synonyms가 비어있으면 경고
- **중복 체크**: 같은 english 단어가 여러 Day에 등장하는지
- **OCR 교정 리스트**: ocr_note가 null이 아닌 단어 목록 출력
- **Quiz 정답 매칭**: Quiz 정답이 실제 동의어와 일치하는지

### C-2. 수동 스팟 체크

- 각 Day에서 **2~3개 단어**를 교재 원본 PDF와 대조
- 특히 확인: 기출/중요동의어 구분, 다의어 분리, 예문 해석 매칭
- 오류율이 높은 청크는 재추출

### C-3. Import

검증 통과 후 CLI import:

```bash
drill wordbank import data/extracted/day01.json --type toefl
drill wordbank import data/extracted/day02.json --type toefl
...
```

---

## OCR 관련 주의사항

| 오류 유형 | 예시 | 대응 |
|----------|------|------|
| 문자 혼동 | l/I/1, o/0, rn/m | AI 프롬프트에서 문맥 교정 지시 |
| 발음기호 깨짐 | [prɑ́mənənt] → 깨진 문자 | AI가 단어로부터 복원 가능 |
| 색상 구분 소실 | 기출/중요동의어 구분 불가 | 레이아웃 설명 첨부 + 프롬프트에 구분 규칙 명시 |
| 한글 깨짐 | 한국어 뜻/해석 오류 | AI가 영어 뜻에서 추론, ocr_note에 기록 |
| 페이지 하단 해석 분리 | 예문과 해석이 다른 페이지 | AI에게 페이지 하단 블록 매칭 지시 |

---

## 파일 구조 (최종)

```
data/
├── extracted/                    # AI 추출 결과 (Day별)
│   ├── day01.json
│   ├── day02.json
│   ├── ...
│   ├── day30.json
│   ├── quiz_day01.json           # Day별 Quiz (단어 JSON에 포함 가능)
│   ├── review_test_01-05.json
│   ├── review_test_06-10.json
│   ├── review_test_11-15.json
│   ├── review_test_16-20.json
│   ├── review_test_21-25.json
│   ├── review_test_26-30.json
│   └── final_tests.json
├── merged/                       # 병합 후 최종 데이터
│   ├── chorogi_words_all.json
│   └── chorogi_tests_all.json
└── sample/                       # 샘플 데이터
    └── chorogi_sample.json
```

## 작업 소요 예상

| 작업 | 소요 시간 |
|------|----------|
| A-2 PDF 분할 (스크립트 자동화) | 10분 |
| A-3~A-4 샘플 추출 + 프롬프트 조정 | 30분 |
| B-1 30개 Day 추출 (AI 반복) | 3~4시간 (AI 응답 대기 포함) |
| B-2~B-3 테스트 추출 | 30분 |
| C-1~C-2 검증 | 1시간 |
| C-3 Import | 10분 |
| **합계** | **약 5~6시간** |

## 이후 단계

데이터 import 완료 후:
- Phase 2-1: FastAPI 서버 구현
- Phase 2-2: SyOps React 모바일 UI
