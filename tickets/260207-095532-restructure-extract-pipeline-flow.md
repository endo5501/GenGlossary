---
priority: 2
tags: [feature, pipeline, frontend, backend]
description: "Restructure extract pipeline: auto-extract on file add, remove extract from Run"
created_at: "2026-02-07T09:55:32Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# ファイル追加と解析処理の操作体系見直し

## 概要

現在の操作フローでは、ファイル追加（Files画面）と用語抽出（Extract）が完全に分離しており、ユーザーは以下の手順を踏む必要がある:

1. Files画面でファイル追加
2. Terms画面でExtract実行
3. 不要な用語を手動除去（LLMだけでは不十分なため、何度か試行）
4. Run（Full Pipeline: extract → generate → review → refine）実行

この手順では **Extractが複数回無駄に実行される** 問題がある:
- ファイル追加後に手動でExtractを実行する必要がある
- Run（Full Pipeline）実行時にも再度Extractが走る

これを以下のように改善する。

## 変更内容

### 変更1: ファイル追加時にExtractを自動実行

Files画面でファイルを追加した際、バックエンドでファイル保存完了後に自動的にExtract処理を開始する。

**現在のフロー:**
```
ファイル追加 → DBに保存 → 完了
（ユーザーがTerms画面に移動して手動Extract）
```

**変更後のフロー:**
```
ファイル追加 → DBに保存 → Extract自動開始 → 完了
```

**実装箇所:**
- バックエンド: `POST /api/projects/{project_id}/files/bulk` (`files.py` router)
  - ファイル保存成功後、`RunManager.start_run(scope='extract')` を呼び出す
- フロントエンド: `AddFileDialog.tsx` / `FilesPage.tsx`
  - ファイル追加成功後、Extractが開始されたことをユーザーに通知（トースト等）
  - 現在の実行状態（`useCurrentRun`）が自動的にExtract進行中を表示

### 変更2: RunのFull Pipelineからextractを除外

RunボタンのFull Pipeline実行時、extractを省略し `generate → review → refine` のみを実行する。

**現在のFull Pipeline:**
```
extract → generate → review → refine
```

**変更後のFull Pipeline:**
```
generate → review → refine
```

**Extractの実行タイミング（変更後）:**
- ファイル追加時（自動）← 変更1で追加
- Terms画面の「Extract」ボタン押下時（手動、既存機能のまま）

**実装箇所:**
- バックエンド: `PipelineExecutor._execute_full()` (`executor.py`)
  - extract ステップを削除し、generate から開始
  - DBに既に用語が存在することを前提とする
- フロントエンド: `GlobalTopBar.tsx` の Scopeセレクター
  - "Full Pipeline" のラベル/説明を更新（extractを含まないことを明示）
  - "Extract Only" はそのまま残す（Terms画面の手動Extractと同等）

## 改善されるフロー（Before/After）

### Before（現在）
```
1. Files画面 → ファイル追加
2. Terms画面 → Extract実行（手動）
3. Terms画面 → 不要用語を除去
4. Run（Full Pipeline）→ extract → generate → review → refine
                         ^^^^^^^^
                         ↑ 無駄な再実行
```

### After（変更後）
```
1. Files画面 → ファイル追加 + Extract自動実行
2. Terms画面 → 不要用語を除去（必要に応じてExtractボタンで再実行も可能）
3. Run（Full Pipeline）→ generate → review → refine
```

## 考慮事項

### Extract自動実行時の実行状態管理
- ファイル追加とExtractは同じレスポンスで返すか、Extractはバックグラウンドで非同期実行か
- 現在のRunManagerは同時に1つのRunのみ許可しているため、既にRunが実行中の場合の扱い
  - 方針: 実行中の場合はExtract自動実行をスキップし、ユーザーに手動Extract を促す

### Full Pipeline実行時に用語が存在しない場合
- DBに用語が存在しない状態でFull Pipelineを実行した場合のエラーハンドリング
- 方針: 用語が0件の場合はエラーメッセージを表示し、先にExtractを実行するよう促す

### Scopeセレクターの整合性
- "Extract Only" スコープはそのまま残す（手動抽出用）
- "Full Pipeline" の内容が変わるため、ラベルや説明文の更新が必要


## Tasks

- [ ] Backend: `PipelineExecutor._execute_full()` からextractステップを除外し、generate開始に変更
- [ ] Backend: Full Pipeline実行時に用語が0件の場合のエラーハンドリング追加
- [ ] Backend: `POST /api/projects/{project_id}/files/bulk` でファイル保存後にExtract自動開始
- [ ] Backend: ファイル追加時、既にRunが実行中の場合のハンドリング（スキップ＋通知）
- [ ] Frontend: `AddFileDialog` / `FilesPage` でファイル追加成功後のExtract開始通知UI
- [ ] Frontend: `GlobalTopBar.tsx` のScopeセレクターのラベル/説明を更新
- [ ] テスト: Full Pipelineがextractをスキップすることの検証
- [ ] テスト: ファイル追加時にExtractが自動実行されることの検証
- [ ] テスト: 用語0件でFull Pipeline実行時のエラーハンドリング検証
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- 除外用語機能との連動: ファイル追加時のExtract自動実行では、既存の除外用語フィルタが適用される
- 今回作成した「追加必須用語一覧」チケット（`260207-093417-required-terms-list`）との依存: 必須用語機能が先に実装されていれば、自動Extract時にも必須用語が反映される
- CLI modeへの影響: CLIでのFull Pipeline実行も同様にextractを除外するか要検討（CLIではファイル読み込みと抽出が一体のため、CLIのみextract付きのフローを維持する選択肢もある）
