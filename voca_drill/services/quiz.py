"""QuizGenerator -- 다차원 퀴즈 생성 + 채점."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from ..data.models import Word, WordMeaning, WordProgress


@dataclass
class QuizItem:
    """생성된 퀴즈 아이템."""

    word_id: int
    quiz_type: str
    question: dict
    choices: list[dict] = field(default_factory=list)
    correct_answer: str = ""


@dataclass
class TypingResult:
    """타이핑 퀴즈 채점 결과."""

    is_correct: bool
    is_close: bool
    user_input: str
    correct_answer: str
    distance: int


QUIZ_TYPE_BY_LEVEL: dict[int, str] = {
    1: "card_flip",
    2: "card_flip",
    3: "multiple_choice",
    4: "reverse",
    5: "typing",
}


class QuizGenerator:
    """mastery_level에 따라 퀴즈를 생성."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def select_quiz_type(self, word: Word) -> str:
        """단어의 mastery_level에 따라 퀴즈 유형 결정."""
        progress = (
            self._session.query(WordProgress)
            .filter(WordProgress.word_id == word.id)
            .first()
        )
        level = progress.mastery_level if progress else 1
        return QUIZ_TYPE_BY_LEVEL.get(level, "card_flip")

    def generate(self, word: Word, quiz_type: str | None = None) -> QuizItem:
        """단어에 대한 퀴즈 아이템 생성."""
        if quiz_type is None:
            quiz_type = self.select_quiz_type(word)

        generators = {
            "card_flip": self._gen_card_flip,
            "multiple_choice": self._gen_multiple_choice,
            "reverse": self._gen_reverse,
            "typing": self._gen_typing,
        }

        generator = generators.get(quiz_type, self._gen_card_flip)
        return generator(word)

    def check_typing(self, correct: str, user_input: str) -> TypingResult:
        """타이핑 퀴즈 채점 (Levenshtein distance 1 허용)."""
        correct_lower = correct.lower().strip()
        input_lower = user_input.lower().strip()

        if correct_lower == input_lower:
            return TypingResult(
                is_correct=True, is_close=False,
                user_input=user_input, correct_answer=correct, distance=0,
            )

        dist = _levenshtein(correct_lower, input_lower)
        is_close = dist <= 1

        return TypingResult(
            is_correct=is_close, is_close=is_close and dist > 0,
            user_input=user_input, correct_answer=correct, distance=dist,
        )

    def _gen_card_flip(self, word: Word) -> QuizItem:
        """카드 플립 -- 앞면: 영어+품사, 뒷면: 동의어+한국어+예문."""
        meanings = self._get_meanings(word)
        primary = meanings[0] if meanings else {}

        return QuizItem(
            word_id=word.id,
            quiz_type="card_flip",
            question={
                "front": {
                    "english": word.english,
                    "pronunciation": word.pronunciation,
                    "part_of_speech": primary.get("part_of_speech", ""),
                },
                "back": {
                    "meanings": meanings,
                    "derivatives": json.loads(word.derivatives_json),
                    "exam_tip": word.exam_tip,
                },
            },
            correct_answer=word.english,
        )

    def _gen_multiple_choice(self, word: Word) -> QuizItem:
        """객관식 -- 동의어를 보여주고 4개 보기 중 원래 단어 선택."""
        meanings = self._get_meanings(word)
        all_synonyms = self._collect_synonyms(meanings, word)

        distractors = self._get_distractors(word, count=3)

        choices = [{"word": word.english, "is_correct": True}]
        for d in distractors:
            choices.append({"word": d.english, "is_correct": False})
        random.shuffle(choices)

        hint_synonyms = all_synonyms[:3] if all_synonyms else []
        primary_korean = meanings[0].get("korean", "") if meanings else ""

        return QuizItem(
            word_id=word.id,
            quiz_type="multiple_choice",
            question={
                "prompt": "다음 동의어에 해당하는 단어를 고르세요.",
                "synonyms": hint_synonyms,
                "korean": primary_korean,
            },
            choices=choices,
            correct_answer=word.english,
        )

    def _gen_reverse(self, word: Word) -> QuizItem:
        """역방향 -- 영영 풀이/동의어를 보고 단어 선택."""
        meanings = self._get_meanings(word)
        primary = meanings[0] if meanings else {}

        english_def = primary.get("english_definition", "")
        all_synonyms = self._collect_synonyms(meanings, word)

        if english_def:
            prompt = english_def
            prompt_type = "english_definition"
        elif all_synonyms:
            prompt = ", ".join(all_synonyms)
            prompt_type = "synonyms"
        else:
            prompt = primary.get("korean", word.english)
            prompt_type = "korean"

        distractors = self._get_distractors(word, count=3)
        choices = [{"word": word.english, "is_correct": True}]
        for d in distractors:
            choices.append({"word": d.english, "is_correct": False})
        random.shuffle(choices)

        return QuizItem(
            word_id=word.id,
            quiz_type="reverse",
            question={
                "prompt": prompt,
                "prompt_type": prompt_type,
            },
            choices=choices,
            correct_answer=word.english,
        )

    def _gen_typing(self, word: Word) -> QuizItem:
        """타이핑 -- 한국어 뜻+동의어를 보고 영어 단어 직접 입력."""
        meanings = self._get_meanings(word)
        primary = meanings[0] if meanings else {}
        all_synonyms = self._collect_synonyms(meanings, word)

        return QuizItem(
            word_id=word.id,
            quiz_type="typing",
            question={
                "korean": primary.get("korean", ""),
                "synonyms": all_synonyms[:3],
                "part_of_speech": primary.get("part_of_speech", ""),
                "hint_length": len(word.english),
            },
            correct_answer=word.english,
        )

    def _get_meanings(self, word: Word) -> list[dict]:
        """Word의 meanings를 dict 리스트로 변환."""
        meanings_orm = (
            self._session.query(WordMeaning)
            .filter(WordMeaning.word_id == word.id)
            .order_by(WordMeaning.meaning_order)
            .all()
        )
        result = []
        for m in meanings_orm:
            result.append({
                "order": m.meaning_order,
                "part_of_speech": m.part_of_speech,
                "korean": m.korean,
                "tested_synonyms": json.loads(m.tested_synonyms_json),
                "important_synonyms": json.loads(m.important_synonyms_json),
                "example_en": m.example_en,
                "example_ko": m.example_ko,
                "english_definition": m.english_definition,
            })
        return result

    def _collect_synonyms(self, meanings: list[dict], word: Word) -> list[str]:
        """mastery_level에 따라 동의어 수집.

        Level 1-3: 기출동의어만
        Level 4-5: 기출 + 중요동의어
        """
        progress = (
            self._session.query(WordProgress)
            .filter(WordProgress.word_id == word.id)
            .first()
        )
        level = progress.mastery_level if progress else 1

        synonyms: list[str] = []
        for m in meanings:
            synonyms.extend(m.get("tested_synonyms", []))
            if level >= 4:
                synonyms.extend(m.get("important_synonyms", []))
        return synonyms

    def _get_distractors(self, word: Word, *, count: int = 3) -> list[Word]:
        """오답 보기 -- 같은 챕터 우선, 부족하면 전체에서."""
        same_chapter = (
            self._session.query(Word)
            .filter(Word.id != word.id, Word.chapter == word.chapter)
            .all()
        )

        if len(same_chapter) >= count:
            return random.sample(same_chapter, count)

        all_others = (
            self._session.query(Word)
            .filter(Word.id != word.id)
            .all()
        )
        if len(all_others) >= count:
            return random.sample(all_others, count)

        return all_others


def _levenshtein(s1: str, s2: str) -> int:
    """Levenshtein distance 계산."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]
