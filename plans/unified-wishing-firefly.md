# コードレビュー指摘事項の修正計画

## 概要
`provisional.py` の regenerate エンドポイントに対するコードレビュー指摘事項3件を修正する。

## 修正対象

### 1. [High] テストの実 LLM 呼び出し除去
**問題**: `test_regenerate_provisional_updates_definition` が実 LLM を呼び出しており、Ollama がない環境で失敗する

**該当ファイル**: `tests/api/routers/test_provisional.py:171-191`

**修正内容**:
- `GlossaryGenerator` をモックして実 LLM 呼び出しを回避
- 既存のモック化テスト (`test_regenerate_provisional_changes_definition_with_mock`) を参考にパッチ追加

### 2. [Medium] doc_root 不正時のエラーハンドリング
**問題**: `DocumentLoader().load_directory()` が例外を投げると 500 になる

**該当ファイル**: `src/genglossary/api/routers/provisional.py:80`

**修正内容**:
- `_regenerate_definition` 関数内で `FileNotFoundError`, `NotADirectoryError` をキャッチ
- 400 Bad Request に変換して返す
- テストケース追加: `test_regenerate_provisional_invalid_doc_root_returns_400`

### 3. [Low] create_llm_client の ValueError 処理
**問題**: 不正な `llm_provider` で ValueError が発生すると 500 になる

**該当ファイル**: `src/genglossary/api/routers/provisional.py:79`

**修正内容**:
- `ValueError` をキャッチして 400 Bad Request に変換
- テストケース追加: `test_regenerate_provisional_invalid_llm_provider_returns_400`

## 修正ファイル一覧
1. `tests/api/routers/test_provisional.py`
   - `test_regenerate_provisional_updates_definition` のモック化
   - 新規テスト2件追加

2. `src/genglossary/api/routers/provisional.py`
   - `_regenerate_definition` のエラーハンドリング追加
   - または `regenerate_provisional` エンドポイント内でキャッチ

## 検証方法
```bash
# テスト実行（Ollama なしで通過することを確認）
uv run pytest tests/api/routers/test_provisional.py -v

# 静的解析
uv run pyright

# 全体テスト
uv run pytest
```
