---
priority: 4.7
tags: [api, llm, provisional]
description: "Implement provisional glossary entry regeneration endpoint with LLM integration"
created_at: "2026-01-25T12:59:01Z"
started_at: 2026-01-25T13:03:13Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Implement the `POST /api/projects/{project_id}/provisional/{entry_id}/regenerate` endpoint
that currently returns TODO placeholder. This endpoint should use LLM (Ollama) to
regenerate a single provisional glossary entry's definition and confidence score.

This is a follow-up from ticket #260124-164009-gui-api-data-endpoints code review.


## Tasks

- [x] **Red**: テスト追加
  - [x] regenerate が実際に定義を変更することを検証するテスト
  - [x] regenerate が confidence を更新することを検証するテスト
  - [x] LLM呼び出しのモックを使用したテスト
  - [x] LLM timeout/error ハンドリングのテスト (503 返却)
  - [x] DB永続化の検証テスト
- [x] テスト失敗確認（Red完了）
- [x] **Implementation**: regenerate endpoint実装
  - [x] LLM client (GlossaryGenerator) を使用して定義を再生成
  - [x] プロジェクトのLLM設定を取得して使用
  - [x] ドキュメントコンテキストを読み込んで渡す
  - [x] 再生成結果をDBに保存
  - [x] LLMエラーハンドリング（timeout, HTTPError → 503）
- [x] **Green**: テスト通過確認
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Update docs/architecture.md (API エンドポイントの説明を更新)
- [ ] Get developer approval before closing


## Notes

### 現状の問題
- `src/genglossary/api/routers/provisional.py:101-128` が TODO で既存値を返している
- `tests/api/routers/test_provisional.py:172-182` が「再生成されたこと」を検証していない

### 実装方針
- LLM統合パターンは `/llm-integration` スキルを参照
- GlossaryGenerator を使用して単一エントリを再生成
- エラーハンドリング（LLMタイムアウト、API失敗など）を適切に実装
- 既存のCLI実装 (`cli_db_regenerate.py`) を参考にする

### Dependencies
- Ticket #260124-164009-gui-api-data-endpoints (完了済み)
- LLM設定がプロジェクトに保存されていること


## 作業結果

### 実装内容

#### Phase 1: Red (コミット: 529a0de)
**テスト追加**: 5つの新しいテストケースを追加
1. `test_regenerate_provisional_changes_definition_with_mock` - LLMをモックして新しい定義を返すことを検証
2. `test_regenerate_provisional_updates_confidence_with_mock` - confidenceが更新されることを検証
3. `test_regenerate_provisional_persists_to_db` - GETで取得して永続化を検証
4. `test_regenerate_provisional_llm_timeout_returns_503` - LLMタイムアウト時に503を返す
5. `test_regenerate_provisional_llm_unavailable_returns_503` - LLM接続エラー時に503を返す

**失敗確認**: 全ての新しいテストが期待通り失敗（`AttributeError: GlossaryGenerator`）

#### Phase 2: Green (コミット: 58b569e)
**実装**: `src/genglossary/api/routers/provisional.py` の `regenerate_provisional` エンドポイント
- 必要なインポート追加（`httpx`, `GlossaryGenerator`, `DocumentLoader`, `create_llm_client`, etc.）
- プロジェクトからLLM設定を取得（`llm_provider`, `llm_model`）
- `DocumentLoader` でドキュメントを読み込み
- `GlossaryGenerator` を使用して用語の出現箇所を検索し、定義を再生成
- 新しい定義とconfidenceでDBを更新
- LLMエラーハンドリング実装（`httpx.TimeoutException`, `httpx.HTTPError` → 503）

**成功確認**: 全てのテストが通過
- `tests/api/routers/test_provisional.py`: 14 passed
- 全体: 581 passed, 6 deselected
- 静的解析: 0 errors, 0 warnings

### 変更ファイル
- `tests/api/routers/test_provisional.py` - テスト追加（+154行）
- `src/genglossary/api/routers/provisional.py` - 実装（TODO削除、LLM統合実装）

### エンドポイント仕様
**URL**: `POST /api/projects/{project_id}/provisional/{entry_id}/regenerate`

**レスポンス**:
- 200: 再生成された用語エントリ（ProvisionalResponse）
- 404: 用語が見つからない場合
- 503: LLMタイムアウトまたは接続エラー

**処理フロー**:
1. 用語の存在確認
2. LLMクライアント作成（プロジェクト設定から）
3. ドキュメントロード
4. GlossaryGeneratorで出現箇所検索と定義生成
5. DB更新
6. 更新後の値を返す

#### Phase 3: Refactor (コミット: db8ae64, 8d25a2b)

**ドキュメント更新** (db8ae64):
- `docs/architecture.md` に regenerate エンドポイントの詳細実装を追加
- 処理フロー、エラーハンドリング、LLM統合ポイントを文書化

**コード簡素化** (8d25a2b):
code-simplifier agentによるリファクタリングを実施

**抽出したヘルパー関数**:
1. `_ensure_term_exists()` - 用語の存在確認と取得（404エラー処理）
2. `_get_term_response()` - レスポンス構築（RuntimeError処理）
3. `_regenerate_definition()` - LLM再生成ロジックのカプセル化

**改善効果**:
- `regenerate_provisional` の行数: 31行 → 10行 (-68%)
- コード重複: 3箇所 → 0箇所 (-100%)
- 単一責任原則の適用、認知的複雑性の削減
- 型アノテーション修正（`GlossaryTermRow`）
- 全テスト通過（14/14）

### 最終結果
- **テスト**: 14/14 passed (provisional API)
- **静的解析**: 0 errors, 0 warnings
- **全体テスト**: 581 passed, 6 deselected
- **コミット数**: 5 (tests, implementation, ticket update, docs, refactor)

### 残タスク
- [ ] 開発者承認
