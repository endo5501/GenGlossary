# Repository Guidelines

## Project Structure & Module Organization
- `src/genglossary/`: core package (LLM clients, extraction, generation, review, CLI).
- `src/genglossary/db/`: SQLite storage and CLI helpers.
- `src/genglossary/llm/`, `src/genglossary/models/`, `src/genglossary/output/`, `src/genglossary/utils/`: submodules for providers, schemas, formatters, utilities.
- `tests/`: pytest suite; integration tests live in `tests/test_ollama_integration.py`.
- `test_ollama_integration.py`: legacy top-level integration test (run with pytest).
- `examples/`: sample input documents for manual runs.
- `target_docs/`: default input documents for CLI runs.
- `output/`: generated glossaries (kept out of tests).
- `docs/`: project documentation (see `docs/architecture.md`).
- `scripts/`: helper scripts for local workflows.
- `tickets/` and `plan.md`: work tracking.

## Build, Test, and Development Commands
- `uv sync`: install dependencies from `pyproject.toml`/`uv.lock`.
- `uv run genglossary generate --input ./target_docs --output ./output/glossary.md`: run the CLI locally.
- `uv run genglossary analyze-terms --input ./target_docs`: inspect term extraction.
- `uv run genglossary db init --path ./genglossary.db`: initialize the SQLite database.
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
