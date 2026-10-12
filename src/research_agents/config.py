import os
from dataclasses import dataclass

DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"
DEFAULT_CLAUDE_MODEL = "claude-opus-5-5"


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    anthropic_api_key: str
    gemini_model: str = DEFAULT_GEMINI_MODEL
    claude_model: str = DEFAULT_CLAUDE_MODEL

    @classmethod
    def from_env(cls) -> "Settings":
        missing = [k for k in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY") if not os.environ.get(k)]
        if missing:
            raise RuntimeError(f"Faltan variables de entorno: {', '.join(missing)}")
        return cls(
            gemini_api_key=os.environ["GEMINI_API_KEY"],
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            gemini_model=os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
            claude_model=os.environ.get("CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL),
        )
