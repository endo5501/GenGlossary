# Repository Guidelines

## Project Structure & Module Organization
- `src/genglossary/`: core package (LLM clients, extraction, generation, review, CLI).
- `tests/`: pytest suite; `test_ollama_integration.py` covers integration behavior.
- `examples/`: sample input documents for manual runs.
- `output/`: generated glossaries (kept out of tests).
- `scripts/`: helper scripts for local workflows.
- `tickets/` and `plan.md`: work tracking.

## Build, Test, and Development Commands
- `uv sync`: install dependencies from `pyproject.toml`/`uv.lock`.
- `uv run genglossary generate --input ./target_docs --output ./output/glossary.md`: run the CLI locally.
- `uv run genglossary analyze-terms --input ./target_docs`: inspect term extraction.
- `uv run pytest`: run the full test suite.
- `uv run pytest --cov=genglossary --cov-report=term-missing`: run tests with coverage.
- `uv run pyright`: run static type checks.

## Coding Style & Naming Conventions
- Python 3.11+; keep modules under `src/genglossary/`.
- Use 4-space indentation and descriptive, lowercase module names.
- Follow Pydantic model conventions for data schemas; prefer explicit types.
- No formatter is enforced in `pyproject.toml`; keep diffs clean and consistent.

## Testing Guidelines
- Framework: `pytest` with `pytest-cov`.
- Place tests in `tests/` and name files `test_*.py`.
- Prefer fast unit tests; integration tests should be marked and documented in the test docstring.

## Commit & Pull Request Guidelines
- Commit messages in history are short, imperative, and sometimes prefixed (e.g., `Refactor:`).
- Keep commits scoped to one logical change; update tickets when relevant.
- PRs should include: a concise summary, test command output, and any required config notes.
- If behavior changes, include before/after examples (CLI command + sample output path).

## Configuration & Secrets
- Copy `.env.example` to `.env` for local runs and set LLM provider keys/URLs.
- Never commit API keys or model credentials; use environment variables instead.
