---
priority: 1
tags: [bug, gui]
description: "GUI: Terms/Issues/Refined画面でエラーまたは何も表示されない"
created_at: "2026-01-29T14:05:04Z"
started_at: 2026-01-29T14:39:09Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# GUI: Terms/Issues/Refined画面でエラーまたは何も表示されない

## 概要

パイプライン実行完了後、以下の問題が発生する：

1. **Terms画面**: "Something went wrong!", "Cannot read properties of undefined (reading 'length')" エラーが表示される
2. **Issues画面**: 何も表示されない
3. **Refined画面**: 何も表示されない

## 再現手順

1. GUIでプロジェクトを作成し、ドキュメントを登録
2. Runボタンを押して実行
3. ログに「completed」と表示された後、各画面に遷移

## 期待される動作

- Terms画面: 抽出された用語のリストが表示される
- Issues画面: レビューで発見された問題のリストが表示される
- Refined画面: 改善された用語集が表示される

## 調査ポイント

### Terms画面のエラー

```
Cannot read properties of undefined (reading 'length')
```

- APIレスポンスの形式が期待と異なる可能性
- undefinedチェックの不足

### Issues/Refined画面

- データがDBに正しく保存されているか確認
- APIエンドポイントが正しくデータを返しているか確認

## Tasks

- [x] Terms画面のエラー原因を調査
- [x] Issues/Refined画面のデータフローを調査
- [x] 修正を実装
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent
- [x] Code review by codex MCP
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing

## 調査結果

### 根本原因

フロントエンドとバックエンドのスキーマ不一致が原因：

| 画面 | 問題 | フロントエンド期待 | バックエンド実態 |
|------|------|------------------|-----------------|
| Terms | `occurrences.length` エラー | `occurrences: TermOccurrence[]` | フィールドなし |
| Issues | 何も表示されない | `severity`, `term_id` | `severity`なし, `term_name`あり |

### 修正内容

1. **`types.ts`**: `IssueResponse` を実際のバックエンドレスポンスに合わせて修正
   - `term_id` → `term_name` に変更
   - `severity` フィールドを削除

2. **`IssuesPage.tsx`**: バックエンドの実際のレスポンスに合わせて修正
   - `term_name` を表示
   - `severity` 関連の表示を削除

3. **`TermsPage.tsx`**: バックエンドの実際のレスポンスに合わせて修正
   - `occurrences` カラムを削除（バックエンドが返さないため）
   - 詳細パネルから `OccurrenceList` を削除

4. **`useTerms.ts`**: 型を `TermDetailResponse` から `TermResponse` に変更

5. **テストの修正**: モックデータをバックエンドの実際のレスポンスに合わせて修正

## 追加調査結果（2026-01-30）

### データベースの状態

実際のプロジェクトDBを調査した結果：

| テーブル | レコード数 |
|---|---|
| terms_extracted | 53 |
| documents | 1 |
| glossary_provisional | 27 |
| glossary_issues | **0** |
| glossary_refined | **0** |

### Issues/Refinedが空の原因

1. **Issuesが0件**: GlossaryReviewerがIssuesを生成していない
   - パイプラインは`completed`で正常終了
   - Issuesが0のため、Refinedステップは実行されない（仕様通り）

2. **Provisionalに無関係な定義が混入**
   - 例：`GenGlossaryプロジェクト`の定義に「アソリウス島騎士団」の説明
   - 原因：`glossary_generator.py`のFew-shot exampleがLLM出力に混入

3. **Issue Typeスキーマ不一致**
   - Backend: `unclear`, `contradiction`, `missing_relation`, `unnecessary`
   - Frontend: `ambiguous`, `inconsistent`, `missing`

### 関連チケット作成

上記の問題は本チケットの範囲を超えるため、別チケットとして作成：

- `260129-153456-llm-fewshot-contamination` - Few-shot exampleがLLM出力に混入
- `260129-153459-issue-type-schema-mismatch` - Issue Typeスキーマ不一致

## Notes

- Run状態が更新されない問題と関連している可能性あり
