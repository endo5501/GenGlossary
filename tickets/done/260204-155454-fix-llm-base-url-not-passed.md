---
priority: 1
tags: [bug, backend, llm]
description: "Project llm_base_url is not passed to LLM client, causing OpenAI-compatible APIs (like llama.cpp) to fail"
created_at: "2026-02-04T15:54:54Z"
started_at: 2026-02-04T15:55:52Z # Do not modify manually
closed_at: 2026-02-05T13:00:31Z # Do not modify manually
---

# Bug: Project llm_base_url not passed to LLM client

## Problem

Web UIでプロジェクトのLLM Settings画面から設定した`Base URL`が、実際のLLMクライアントに渡されていない。そのため、llama.cppのllama-serverなどOpenAI互換APIを使用する場合に接続に失敗する。

## Root Cause

設定値が以下の経路で伝播されるべきだが、途中で途切れている：

1. **Project model** (`src/genglossary/models/project.py:51`)
   - `llm_base_url: str = ""` フィールドが存在 ✅

2. **dependencies.py** (`src/genglossary/api/dependencies.py:142-148`)
   - `RunManager`作成時に`llm_base_url`を渡していない ❌
   ```python
   manager = RunManager(
       db_path=project.db_path,
       doc_root=project.doc_root,
       llm_provider=project.llm_provider,
       llm_model=project.llm_model,
       # llm_base_url が欠落
   )
   ```

3. **RunManager** (`src/genglossary/runs/manager.py`)
   - `llm_base_url`パラメータが`__init__`に存在しない ❌

4. **PipelineExecutor** (`src/genglossary/runs/executor.py:140`)
   - `create_llm_client`呼び出し時に`openai_base_url`を渡していない ❌

5. **create_llm_client** (`src/genglossary/llm/factory.py:38`)
   - `openai_base_url`がNoneの場合、環境変数`OPENAI_BASE_URL`のデフォルト値を使用


## Tasks

- [x] `RunManager.__init__`に`llm_base_url`パラメータを追加
- [x] `dependencies.py`の`_create_and_register_manager`で`llm_base_url`を渡す
- [x] `_settings_match`関数で`llm_base_url`の比較を追加
- [x] `PipelineExecutor.__init__`に`base_url`パラメータを追加
- [x] `PipelineExecutor`の`create_llm_client`呼び出しで`openai_base_url`を渡す
- [x] テストを追加・更新
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
  - Codex found CLI issue with openai_base_url → Fixed in commit 0a5b300
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

### Workaround

修正されるまでの回避策として、環境変数を設定してバックエンドを起動：

```bash
OPENAI_BASE_URL=http://127.0.0.1:8080/v1 uv run uvicorn genglossary.api.app:app --reload
```

### Affected Files

- `src/genglossary/llm/factory.py` - `openai_base_url`を`base_url`にリネーム、Ollamaにも適用
- `src/genglossary/llm/openai_compatible_client.py` - `stream: false`と`max_tokens`を追加（llama.cpp対応）
- `src/genglossary/runs/executor.py` - `base_url`パラメータを追加
- `src/genglossary/runs/manager.py` - `llm_base_url`パラメータを追加、コンソールエラーログを追加
- `src/genglossary/api/dependencies.py` - `llm_base_url`を渡す、`_settings_match`を更新

### Additional Fixes

llama.cppのllama-server使用時にJSONレスポンスが途中で切れる問題を修正：
- `OpenAICompatibleClient`に`stream: false`を明示的に追加
- `max_tokens: 4096`をデフォルトで追加（llama-serverのデフォルト制限を回避）

### Design

```
Project.llm_base_url
    ↓
dependencies._create_and_register_manager(llm_base_url=project.llm_base_url)
    ↓
RunManager(llm_base_url=...)
    ↓
PipelineExecutor(base_url=self.llm_base_url)
    ↓
create_llm_client(base_url=...)
    ↓
OllamaClient(base_url=...) / OpenAICompatibleClient(base_url=...)
```
