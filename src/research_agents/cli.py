import argparse
import sys
from pathlib import Path

from .agents import ClaudeCritic, GeminiExplorer
from .config import Settings
from .orchestrator import Round, run_research


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="research-agents",
        description="Investigación colaborativa: Gemini (Explorador) + Claude (Crítico).",
    )
    parser.add_argument("question", help="Pregunta o tema a investigar")
    parser.add_argument("-r", "--rounds", type=int, default=3, help="Máximo de rondas (por defecto 3)")
    parser.add_argument("-o", "--output", type=Path, help="Guardar el informe en este archivo .md")
    parser.add_argument("--no-search", action="store_true", help="No usar Google Search en el Explorador")
    args = parser.parse_args(argv)

    try:
        settings = Settings.from_env()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    explorer = GeminiExplorer(
        settings.gemini_api_key, settings.gemini_model, search=settings.gemini_search and not args.no_search
    )
    critic = ClaudeCritic(settings.anthropic_api_key, settings.claude_model)

    def report(r: Round) -> None:
        mark = "aprobado" if r.critique.approved else "pide cambios"
        print(f"[ronda {r.number}] Crítico: {r.critique.score}/10, {mark}", file=sys.stderr)

    result = run_research(args.question, explorer, critic, args.rounds, on_round=report)
    markdown = result.to_markdown()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(f"Informe guardado en {args.output}", file=sys.stderr)
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
