"""Explorer/Critic loop."""

from collections.abc import Callable
from dataclasses import dataclass, field

from .agents import Critic, Critique, Explorer


@dataclass
class Round:
    number: int
    draft: str
    critique: Critique


@dataclass
class ResearchResult:
    question: str
    rounds: list[Round] = field(default_factory=list)

    @property
    def final_draft(self) -> str:
        return self.rounds[-1].draft if self.rounds else ""

    @property
    def approved(self) -> bool:
        return bool(self.rounds) and self.rounds[-1].critique.approved

    def to_markdown(self) -> str:
        status = "Aprobado por el Crítico" if self.approved else "No aprobado (límite de rondas)"
        last = self.rounds[-1].critique if self.rounds else None
        lines = [
            f"# Investigación: {self.question}",
            "",
            f"**Estado:** {status} · **Rondas:** {len(self.rounds)}"
            + (f" · **Puntuación final:** {last.score}/10" if last else ""),
            "",
            self.final_draft,
            "",
            "---",
            "",
            "## Historial de revisiones",
        ]
        for r in self.rounds:
            lines += [
                "",
                f"### Ronda {r.number} — {r.critique.score}/10"
                + (" ✅" if r.critique.approved else ""),
                "",
                r.critique.feedback or "_(sin comentarios)_",
            ]
        return "\n".join(lines) + "\n"


def run_research(
    question: str,
    explorer: Explorer,
    critic: Critic,
    max_rounds: int = 3,
    on_round: Callable[[Round], None] | None = None,
) -> ResearchResult:
    if max_rounds < 1:
        raise ValueError("max_rounds must be >= 1")
    result = ResearchResult(question=question)
    draft: str | None = None
    feedback: str | None = None
    for number in range(1, max_rounds + 1):
        draft = explorer.explore(question, draft, feedback)
        critique = critic.review(question, draft)
        round_ = Round(number, draft, critique)
        result.rounds.append(round_)
        if on_round:
            on_round(round_)
        if critique.approved:
            break
        feedback = critique.feedback
    return result
