---
priority: 1
tags: [bug, gui]
description: "GUI: Run実行時に「No documents found」エラーが発生する問題"
created_at: "2026-01-29T13:37:03Z"
started_at: 2026-01-29T13:40:50Z # Do not modify manually
closed_at: 2026-01-29T14:18:17Z # Do not modify manually
---

# GUI: Run実行時に「No documents found」エラーが発生する問題

## 概要

GUI機能でOllama利用のプロジェクトを作成し、テキストファイルを登録してRunボタンを押したところ、以下のエラーが発生して処理が停止する。STOPボタンを押しても反応がない。

### 再現手順

1. GUIでOllama利用のプロジェクトを作成
2. テキストファイルを1つ登録
3. 全体実行のRunボタンを押す

### 発生するエラーログ

```
[INFO] Starting pipeline execution: full
[INFO] Loading documents...
[ERROR] No documents found
[ERROR] Run failed: No documents found in doc_root
```

### 期待される動作

- 登録したテキストファイルが正しく読み込まれ、用語抽出処理が開始される
- STOPボタンが押されたら処理が中断される

## 調査結果

### エラー発生箇所

`src/genglossary/runs/executor.py` の `_execute_full()` メソッド（行174-176）:

```python
if not documents:
    self._log("error", "No documents found")
    raise RuntimeError("No documents found in doc_root")
```

### 問題の原因

**根本原因**: GUI mode と CLI mode の判定ロジックが不正確

`executor.py` 行167の判定ロジック:
```python
use_filesystem = doc_root != "."
```

**問題のメカニズム**:

1. GUIでプロジェクト作成 → `doc_root` は `~/.genglossary/projects/MyProject` に自動設定される
2. ユーザーがGUIでテキストファイルをアップロード → **DBに保存される**
3. ユーザーがRunボタンを押す
4. `use_filesystem = doc_root != "."` チェック → **True** (doc_root は `~/.genglossary/projects/...`)
5. **誤ってCLI modeとして実行** → ファイルシステムから読み込もうとする
6. ファイルシステム上には**ドキュメントが存在しない**（DBにのみ存在）
7. `RuntimeError("No documents found in doc_root")` が発生

**c364d0bコミットの問題**:

- `doc_root != "."` という判定では GUI/CLI を正しく区別できない
- GUIで自動生成される `doc_root` は `"."` ではないため、常にCLI modeとして判定される

### GUI vs CLI モードの違い

| モード | doc_root の値 | ドキュメント保存先 |
|--------|---------------|------------------|
| GUI | `~/.genglossary/projects/ProjectName` (自動生成) | DB |
| CLI | ユーザー指定のパス | ファイルシステム |

## 対策

### 方針

GUI mode か CLI mode かを正確に判定するロジックに修正する。

**選択肢**:
1. **DB優先アプローチ（推奨）**: まずDBからドキュメント取得を試み、存在しなければファイルシステムから読み込む
2. `doc_root` が `~/.genglossary/projects/` パス下かどうかでモードを判定
3. 実行時に明示的なモードフラグを渡す

**推奨案（選択肢1: DB優先アプローチ）**:

```python
# まずDBからドキュメント読み込みを試みる
documents = self._load_documents_from_db(conn)

# DBにドキュメントがなく、doc_rootが指定されている場合はFSから読み込む
if not documents and doc_root and doc_root != ".":
    loader = DocumentLoader()
    documents = loader.load_directory(doc_root)

    if documents:
        # FSから読み込んだドキュメントをDBに保存
        delete_all_documents(conn)
        for document in documents:
            create_document(conn, ...)

if not documents:
    raise RuntimeError("No documents found")
```

## 作業手順

### Phase 1: テスト作成（TDD Red） ✅
- [x] GUI mode（DBにドキュメントあり）のテストケース追加
- [x] CLI mode（FSにドキュメントあり）のテストケース追加
- [x] 両方ともドキュメントがない場合のエラーテスト
- [x] テスト失敗を確認してコミット (3c925fc)

### Phase 2: 実装（TDD Green） ✅
- [x] `executor.py` の `_execute_full()` メソッドを修正
- [x] DB優先アプローチでドキュメント読み込みロジックを実装
- [x] テストがパスすることを確認してコミット (3556f42)

### Phase 3: 検証 ✅
- [x] `uv run pytest` で全テストパス確認 (686 passed)
- [x] `pnpm test` でフロントエンドテストパス確認 (137 passed)
- [x] `pyright` で静的解析パス確認 (0 errors)
- [x] GUIで実際に動作確認（メイン問題は解決、追加問題は別チケット化）

### Phase 4: レビュー・ドキュメント更新 ✅
- [x] code-simplifier agent でコード簡素化レビュー（`_load_documents()`に統合）
- [x] codex MCP でコードレビュー（ポータビリティ問題を修正）
- [x] `docs/architecture/runs.md` 更新

## Tasks

- [x] 問題の原因を特定する
- [x] Phase 1: テスト作成（TDD Red）
- [x] Phase 2: 実装（TDD Green）
- [x] Phase 3: 検証
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

### 関連ファイル

- **修正対象**: `src/genglossary/runs/executor.py` (行166-187)
- **テストファイル**: `tests/runs/test_executor.py`
- **関連**: `src/genglossary/runs/manager.py`, `src/genglossary/api/dependencies.py`

### 参考コミット

- c364d0b: Fix GUI bugs: document persistence, Run execution, and cache invalidation
  - このコミットで `use_filesystem = doc_root != "."` ロジックが導入された
  - GUI mode を正しく検出できないバグを含んでいる
