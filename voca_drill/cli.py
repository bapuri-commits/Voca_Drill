"""Voca_Drill CLI 진입점."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .config import load_config
from .data.database import get_session, init_db
from .services.wordbank import WordBank

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

app = typer.Typer(
    name="drill",
    help="공인영어시험 단어 학습 프로그램",
)
wordbank_app = typer.Typer(help="단어장 관리")
app.add_typer(wordbank_app, name="wordbank")

console = Console(force_terminal=True)


def _get_wordbank() -> WordBank:
    config = load_config()
    db_path = config["db"]["path"]
    init_db(db_path)
    session = get_session(db_path)
    return WordBank(session)


@wordbank_app.command("import")
def wordbank_import(
    file: Path = typer.Argument(..., help="JSON 파일 경로", exists=True),
    exam_type: str = typer.Option("toefl", "--type", "-t", help="시험 유형 (toefl/toeic)"),
) -> None:
    """JSON 파일에서 단어를 DB에 import."""
    wb = _get_wordbank()
    result = wb.import_from_json(file, exam_type=exam_type)
    console.print(
        f"[green]import 완료[/green]: "
        f"{result['imported']}개 추가, {result['skipped']}개 스킵 (중복/빈 항목)"
    )


@wordbank_app.command("list")
def wordbank_list(
    chapter: str | None = typer.Option(None, "--chapter", "-c", help="챕터 필터"),
    exam_type: str | None = typer.Option(None, "--type", "-t", help="시험 유형"),
    limit: int = typer.Option(57, "--limit", "-n", help="표시 개수"),
) -> None:
    """등록된 단어 목록 조회."""
    wb = _get_wordbank()
    words = wb.list_words(chapter=chapter, exam_type=exam_type, limit=limit)

    if not words:
        console.print("[yellow]등록된 단어가 없습니다.[/yellow]")
        return

    table = Table(title=f"단어 목록 ({len(words)}개)")
    table.add_column("#", style="dim", width=4)
    table.add_column("단어", style="bold cyan")
    table.add_column("챕터", width=8)
    table.add_column("뜻", min_width=20)
    table.add_column("기출동의어", min_width=25)
    table.add_column("빈도", width=3)

    for w in words:
        meanings_str = " / ".join(
            f"[{m.part_of_speech}] {m.korean}" for m in w.meanings
        )
        tested_all: list[str] = []
        for m in w.meanings:
            tested_all.extend(json.loads(m.tested_synonyms_json))
        tested_str = ", ".join(tested_all[:5])
        if len(tested_all) > 5:
            tested_str += f" (+{len(tested_all) - 5})"

        table.add_row(
            str(w.word_order),
            w.english,
            w.chapter,
            meanings_str,
            tested_str,
            "*" * w.frequency,
        )

    console.print(table)

    total = wb.count_words(exam_type=exam_type)
    if total > len(words):
        console.print(f"[dim]전체 {total}개 중 {len(words)}개 표시[/dim]")


@wordbank_app.command("chapters")
def wordbank_chapters(
    exam_type: str | None = typer.Option(None, "--type", "-t", help="시험 유형"),
) -> None:
    """등록된 챕터 목록."""
    wb = _get_wordbank()
    chapters = wb.get_chapters(exam_type=exam_type)

    if not chapters:
        console.print("[yellow]등록된 챕터가 없습니다.[/yellow]")
        return

    for ch in chapters:
        count = wb.count_words(chapter=ch, exam_type=exam_type)
        console.print(f"  {ch}: {count}개")


@wordbank_app.command("show")
def wordbank_show(
    word: str = typer.Option(..., "--word", "-w", help="조회할 영어 단어"),
) -> None:
    """단어 상세 조회."""
    wb = _get_wordbank()
    w = wb.get_word_by_english(word)

    if not w:
        console.print(f"[red]'{word}' 단어를 찾을 수 없습니다.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]{w.english}[/bold cyan]  {'*' * w.frequency}")
    if w.pronunciation:
        console.print(f"  발음: {w.pronunciation}")

    derivatives = json.loads(w.derivatives_json)
    if derivatives:
        deriv_str = ", ".join(
            f"{d['pos']} {d['word']}" if isinstance(d, dict) else str(d)
            for d in derivatives
        )
        console.print(f"  파생어: {deriv_str}")

    console.print(f"  챕터: {w.chapter} | 순서: {w.word_order} | 시험: {w.exam_type}")

    for m in w.meanings:
        tested = json.loads(m.tested_synonyms_json)
        important = json.loads(m.important_synonyms_json)
        console.print(f"\n  [bold]{m.meaning_order}. [{m.part_of_speech}] {m.korean}[/bold]")
        if tested:
            console.print(f"     기출: [green]{', '.join(tested)}[/green]")
        if important:
            console.print(f"     중요: [blue]{', '.join(important)}[/blue]")
        if m.example_en:
            console.print(f"     예문: [dim]{m.example_en}[/dim]")
        if m.example_ko:
            console.print(f"     해석: [dim]{m.example_ko}[/dim]")
        if m.english_definition:
            console.print(f"     영영: {m.english_definition}")

    if w.exam_tip:
        console.print(f"\n  [yellow]출제 포인트: {w.exam_tip}[/yellow]")

    console.print()


if __name__ == "__main__":
    app()
