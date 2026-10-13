"""The two agents: a Gemini Explorer and a Claude Critic."""

import json
import re
import time
from dataclasses import dataclass
from typing import Protocol

EXPLORER_SYSTEM = """You are the Explorer in a two-agent research team.
Investigate the user's question thoroughly. Produce a
well-structured Markdown research draft with clear sections, concrete facts,
figures and dates, and cite your sources inline as [n] with a "Sources" list
at the end. When you receive critique from the Critic, revise the draft to
address every point: fix errors, fill gaps, add or replace weak sources.
Reply in the same language as the question."""

CRITIC_SYSTEM = """You are the Critic in a two-agent research team. The
Explorer has written a research draft. Review it rigorously for factual
accuracy, unsupported claims, missing perspectives or counter-evidence, weak
or missing sources, logical gaps and clarity.

Respond ONLY with a JSON object:
{"approved": <true if the draft is ready to publish as-is, else false>,
 "score": <integer 1-10>,
 "feedback": "<specific, actionable numbered list of issues to fix>"}
Write the feedback in the same language as the question."""


@dataclass
class Critique:
    approved: bool
    score: int
    feedback: str


class Explorer(Protocol):
    def explore(self, question: str, draft: str | None = None, critique: str | None = None) -> str: ...


class Critic(Protocol):
    def review(self, question: str, draft: str) -> Critique: ...


def build_explorer_prompt(question: str, draft: str | None, critique: str | None) -> str:
    if draft is None:
        return f"Research question:\n{question}"
    return (
        f"Research question:\n{question}\n\n"
        f"Your previous draft:\n{draft}\n\n"
        f"Critique to address:\n{critique}\n\n"
        "Write the full revised draft."
    )


def parse_critique(text: str) -> Critique:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        data = json.loads(match.group(0)) if match else {}
    except json.JSONDecodeError:
        data = {}
    if not data:
        # Unparseable reply: keep it as feedback and ask for another round.
        return Critique(approved=False, score=0, feedback=text.strip())
    return Critique(
        approved=bool(data.get("approved", False)),
        score=int(data.get("score", 0)),
        feedback=str(data.get("feedback", "")).strip(),
    )


class GeminiExplorer:
    def __init__(self, api_key: str, model: str, search: bool = True, retries: int = 3):
        from google import genai
        from google.genai import errors, types

        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._retries = retries
        self._server_error = errors.ServerError
        # Google Search grounding has no free-tier quota on some accounts.
        self._config = types.GenerateContentConfig(
            system_instruction=EXPLORER_SYSTEM,
            tools=[types.Tool(google_search=types.GoogleSearch())] if search else None,
        )

    def explore(self, question: str, draft: str | None = None, critique: str | None = None) -> str:
        for attempt in range(self._retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=build_explorer_prompt(question, draft, critique),
                    config=self._config,
                )
                return (response.text or "").strip()
            except self._server_error:
                # 503 "high demand" is common on new models; back off and retry.
                if attempt == self._retries - 1:
                    raise
                time.sleep(5 * 2**attempt)
        raise AssertionError("unreachable")


class ClaudeCritic:
    def __init__(self, api_key: str, model: str, max_tokens: int = 4096):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def review(self, question: str, draft: str) -> Critique:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=CRITIC_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Research question:\n{question}\n\nDraft to review:\n{draft}",
            }],
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        return parse_critique(text)
