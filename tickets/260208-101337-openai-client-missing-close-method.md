---
priority: 3
tags: [backend, bug-prevention]
description: "Add close() method to OpenAICompatibleClient to properly release HTTP resources"
created_at: "2026-02-08T10:13:37Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Add close() to OpenAICompatibleClient

## Overview

`OpenAICompatibleClient` does not override `close()` from `BaseLLMClient`. The base implementation is a no-op, so when using `provider="openai"`, neither `cancel_run()` nor `_execute_run`'s finally block actually closes the underlying HTTP client.

## Related Files

- `src/genglossary/llm/openai_compatible_client.py` - missing `close()` override
- `src/genglossary/llm/base.py` - `BaseLLMClient.close()` (no-op default)
- `src/genglossary/llm/ollama_client.py` - reference implementation with `close()`

## Current Behavior

`BaseLLMClient.close()` does nothing. `OllamaClient` overrides it to close the httpx client. `OpenAICompatibleClient` does not override it, so HTTP connections may leak.

## Proposed Solution

Add `close()` to `OpenAICompatibleClient` that closes its httpx client, matching the pattern in `OllamaClient`.

## Tasks

- [ ] Add `close()` method to `OpenAICompatibleClient`
- [ ] Add test for proper resource cleanup
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

Discovered during codex MCP review of ticket 260205-231254-executor-resource-leak.
