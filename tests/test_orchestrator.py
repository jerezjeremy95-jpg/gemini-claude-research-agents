import pytest

from research_agents import run_research
from research_agents.agents import Critique, build_explorer_prompt, parse_critique


class FakeExplorer:
    def __init__(self):
        self.calls = []

    def explore(self, question, draft=None, critique=None):
        self.calls.append((draft, critique))
        return f"draft {len(self.calls)}"


class FakeCritic:
    def __init__(self, approve_on):
        self.approve_on = approve_on
        self.n = 0

    def review(self, question, draft):
        self.n += 1
        return Critique(self.n == self.approve_on, self.n * 3, f"fix {self.n}")


def test_stops_when_approved_and_passes_feedback():
    explorer = FakeExplorer()
    result = run_research("q", explorer, FakeCritic(approve_on=2), max_rounds=5)
    assert len(result.rounds) == 2
    assert result.approved
    assert result.final_draft == "draft 2"
    assert explorer.calls == [(None, None), ("draft 1", "fix 1")]


def test_stops_at_max_rounds():
    result = run_research("q", FakeExplorer(), FakeCritic(approve_on=99), max_rounds=3)
    assert len(result.rounds) == 3
    assert not result.approved
    md = result.to_markdown()
    assert "No aprobado" in md and "### Ronda 3" in md


def test_rejects_zero_rounds():
    with pytest.raises(ValueError):
        run_research("q", FakeExplorer(), FakeCritic(1), max_rounds=0)


def test_parse_critique_json_in_fence():
    c = parse_critique('```json\n{"approved": true, "score": 9, "feedback": "ok"}\n```')
    assert c == Critique(True, 9, "ok")


def test_parse_critique_garbage_is_not_approved():
    c = parse_critique("not json at all")
    assert not c.approved and c.feedback == "not json at all"


def test_explorer_prompt_includes_critique_on_revision():
    assert "Critique to address" not in build_explorer_prompt("q", None, None)
    assert "fix this" in build_explorer_prompt("q", "d", "fix this")
