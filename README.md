# gemini-claude-research-agents

Dual-agent research system: Gemini Pro as Explorer + Claude Pro as Critic for collaborative investigations.

## Cómo funciona

1. **Explorador (Gemini):** investiga la pregunta con Google Search y escribe un borrador en Markdown con fuentes citadas.
2. **Crítico (Claude):** revisa el borrador (exactitud, afirmaciones sin respaldo, huecos, fuentes) y responde con una puntuación de 1 a 10, aprobado o no, y una lista de correcciones.
3. Si no lo aprueba, el Explorador revisa el borrador con esa crítica. El ciclo se repite hasta que el Crítico aprueba o se llega al máximo de rondas.
4. El resultado es un informe en Markdown con el borrador final y el historial de revisiones.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuración

Exporta tus claves de API (consulta `.env.example`):

```bash
export GEMINI_API_KEY=...       # https://aistudio.google.com/apikey
export ANTHROPIC_API_KEY=...    # https://console.anthropic.com/
# Opcionales:
export GEMINI_MODEL=gemini-3.1-pro-preview
export CLAUDE_MODEL=claude-sonnet-5-5
```

## Uso

```bash
research-agents "¿Cuál es el impacto de la IA generativa en el marketing digital en República Dominicana?" \
  --rounds 3 --output reports/ia-marketing.md
```

- `--rounds / -r`: máximo de rondas Explorador → Crítico (por defecto 3).
- `--output / -o`: guarda el informe; sin esta opción se imprime en pantalla.

También puedes usarlo desde Python:

```python
from research_agents import run_research
from research_agents.agents import GeminiExplorer, ClaudeCritic

result = run_research("tu pregunta", GeminiExplorer(key, "gemini-3.1-pro-preview"),
                      ClaudeCritic(key, "claude-sonnet-5-5"), max_rounds=3)
print(result.to_markdown())
```

## Tests

```bash
pip install -e '.[dev]'
pytest
```
