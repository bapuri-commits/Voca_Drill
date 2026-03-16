"""WordBank — 단어 DB CRUD, JSON import."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..data.models import Word, WordMeaning, WordProgress


class WordBank:
    """단어 관리 서비스. DB CRUD + JSON import."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def import_from_json(
        self,
        file_path: str | Path,
        *,
        exam_type: str = "toefl",
        source: str = "import",
    ) -> dict[str, int]:
        """JSON 파일에서 단어를 DB에 import.

        Returns:
            {"imported": N, "skipped": N} — 결과 요약
        """
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            words_data: list[dict[str, Any]] = json.load(f)

        imported = 0
        skipped = 0

        for entry in words_data:
            english = entry.get("english", "").strip()
            if not english:
                skipped += 1
                continue

            existing = self._session.execute(
                select(Word).where(
                    Word.english == english,
                    Word.exam_type == entry.get("exam_type", exam_type),
                )
            ).scalar_one_or_none()

            if existing:
                skipped += 1
                continue

            word = self._build_word(entry, exam_type=exam_type, source=source)
            self._session.add(word)
            imported += 1

        self._session.commit()
        return {"imported": imported, "skipped": skipped}

    def list_words(
        self,
        *,
        chapter: str | None = None,
        exam_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Word]:
        """단어 목록 조회 (필터링 + 페이지네이션)."""
        stmt = (
            select(Word)
            .options(selectinload(Word.meanings), selectinload(Word.progress))
            .order_by(Word.chapter, Word.word_order)
        )

        if chapter:
            stmt = stmt.where(Word.chapter == chapter)
        if exam_type:
            stmt = stmt.where(Word.exam_type == exam_type)
        if status:
            if status == "new":
                stmt = stmt.outerjoin(Word.progress).where(
                    or_(WordProgress.status == "new", WordProgress.id.is_(None))
                )
            else:
                stmt = stmt.join(Word.progress).where(WordProgress.status == status)

        stmt = stmt.offset(offset).limit(limit)
        return list(self._session.execute(stmt).scalars().all())

    def get_word(self, word_id: int) -> Word | None:
        """단어 상세 조회 (meanings, progress 포함)."""
        stmt = (
            select(Word)
            .options(selectinload(Word.meanings), selectinload(Word.progress))
            .where(Word.id == word_id)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_word_by_english(self, english: str) -> Word | None:
        """영어 단어명으로 조회."""
        stmt = (
            select(Word)
            .options(selectinload(Word.meanings), selectinload(Word.progress))
            .where(Word.english == english)
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def count_words(
        self,
        *,
        chapter: str | None = None,
        exam_type: str | None = None,
    ) -> int:
        """단어 수 카운트."""
        stmt = select(func.count(Word.id))
        if chapter:
            stmt = stmt.where(Word.chapter == chapter)
        if exam_type:
            stmt = stmt.where(Word.exam_type == exam_type)
        result = self._session.execute(stmt).scalar()
        return result or 0

    def delete_word(self, word_id: int) -> bool:
        """단어 삭제 (cascade로 meanings, progress도 삭제)."""
        word = self._session.get(Word, word_id)
        if not word:
            return False
        self._session.delete(word)
        self._session.commit()
        return True

    def get_chapters(self, exam_type: str | None = None) -> list[str]:
        """등록된 챕터 목록."""
        stmt = select(Word.chapter).distinct().order_by(Word.chapter)
        if exam_type:
            stmt = stmt.where(Word.exam_type == exam_type)
        return list(self._session.execute(stmt).scalars().all())

    @staticmethod
    def _build_word(entry: dict[str, Any], *, exam_type: str, source: str) -> Word:
        """JSON 엔트리 → Word ORM 객체 변환."""
        derivatives = entry.get("derivatives", [])

        word = Word(
            english=entry["english"].strip(),
            pronunciation=entry.get("pronunciation", ""),
            importance=entry.get("importance", 0),
            derivatives_json=json.dumps(derivatives, ensure_ascii=False),
            exam_type=entry.get("exam_type", exam_type),
            chapter=entry.get("chapter", ""),
            word_order=entry.get("word_order", 0),
            exam_tip=entry.get("exam_tip"),
            source=source,
        )

        for m in entry.get("meanings", []):
            synonyms = m.get("synonyms", [])
            meaning = WordMeaning(
                meaning_order=m.get("order", 1),
                part_of_speech=m.get("part_of_speech", ""),
                korean=m.get("korean", ""),
                synonyms_json=json.dumps(synonyms, ensure_ascii=False),
                example=m.get("example", ""),
                english_definition=m.get("english_definition"),
            )
            word.meanings.append(meaning)

        if not entry.get("meanings"):
            word.meanings.append(WordMeaning(
                meaning_order=1,
                korean=entry.get("korean", ""),
                part_of_speech=entry.get("part_of_speech", ""),
            ))

        return word
