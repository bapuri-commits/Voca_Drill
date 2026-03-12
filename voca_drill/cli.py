"""Voca_Drill CLI 진입점."""

import typer

app = typer.Typer(
    name="drill",
    help="공인영어시험 단어 학습 프로그램",
)


@app.command()
def start(
    type: str = typer.Option(None, help="시험 유형 (toefl/toeic)"),
    count: int = typer.Option(20, help="세션 단어 수"),
    mode: str = typer.Option("en2kr", help="모드 (en2kr/kr2en)"),
    weak_only: bool = typer.Option(False, help="약점 단어만"),
    new_only: bool = typer.Option(False, help="새 단어만"),
) -> None:
    """학습 세션 시작."""
    typer.echo("start 명령 — 아직 구현되지 않았습니다.")


@app.command()
def review(
    last: int = typer.Option(1, help="최근 N세션의 오답"),
) -> None:
    """오답 복습."""
    typer.echo("review 명령 — 아직 구현되지 않았습니다.")


@app.command()
def weak() -> None:
    """약점 단어 목록."""
    typer.echo("weak 명령 — 아직 구현되지 않았습니다.")


@app.command()
def stats(
    today: bool = typer.Option(False, help="오늘 학습만"),
    type: str = typer.Option(None, help="시험 유형"),
) -> None:
    """학습 통계."""
    typer.echo("stats 명령 — 아직 구현되지 않았습니다.")


if __name__ == "__main__":
    app()
