---
priority: 2
tags: [bug, frontend, backend, schema]
description: "Frontend/Backend間でIssue Typeのスキーマが不一致"
created_at: "2026-01-29T15:34:59Z"
started_at: 2026-01-29T16:05:30Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# Frontend/Backend間でIssue Typeのスキーマが不一致

## 概要

フロントエンドとバックエンドでIssue Typeの値が異なり、フィルター機能と色表示が正しく動作しない。

## 現象

1. IssuesページのTypeフィルターが機能しない
2. Issue Typeの色表示がデフォルトのgrayになる

## スキーマの不一致

| バックエンド (`glossary_reviewer.py`) | フロントエンド (`colors.ts`, `IssuesPage.tsx`) |
|---|---|
| `unclear` | `ambiguous` |
| `contradiction` | `inconsistent` |
| `missing_relation` | `missing` |
| `unnecessary` | (対応なし) |

### バックエンド定義

`src/genglossary/models/glossary.py:10`:
```python
IssueType = Literal["unclear", "contradiction", "missing_relation", "unnecessary"]
```

### フロントエンド定義

`frontend/src/utils/colors.ts:15-20`:
```typescript
export type IssueType = 'ambiguous' | 'inconsistent' | 'missing'
export const issueTypeColors: Record<IssueType, string> = {
  ambiguous: 'orange',
  inconsistent: 'grape',
  missing: 'cyan',
}
```

`frontend/src/pages/IssuesPage.tsx:21-26`:
```typescript
const issueTypeOptions = [
  { value: '', label: 'All Types' },
  { value: 'ambiguous', label: 'Ambiguous' },
  { value: 'inconsistent', label: 'Inconsistent' },
  { value: 'missing', label: 'Missing' },
]
```

## 提案する修正

**Option A: フロントエンドをバックエンドに合わせる**
- `colors.ts` の `IssueType` を更新
- `IssuesPage.tsx` のフィルターオプションを更新

**Option B: バックエンドをフロントエンドに合わせる**
- `glossary_reviewer.py` の Issue Type を変更
- `glossary.py` の `IssueType` 定義を変更

**推奨: Option A**
- バックエンド側の名前（`unclear`, `contradiction` など）の方が意味が明確
- バックエンドの変更はDBスキーマに影響する可能性

## 影響範囲

### フロントエンド
- `frontend/src/utils/colors.ts`
- `frontend/src/pages/IssuesPage.tsx`
- `frontend/src/mocks/handlers.ts`
- `frontend/src/__tests__/terms-workflow.test.tsx`

### バックエンド（Option Bの場合）
- `src/genglossary/models/glossary.py`
- `src/genglossary/glossary_reviewer.py`

## Tasks

- [x] スキーマ統一方針を決定（Option A or B） → **Option A: フロントエンドをバックエンドに合わせる**
- [x] 選択したオプションに基づいて修正
- [x] フィルター機能のテストを追加
- [x] Issues画面にアイテムが表示されることを確認 → **手動確認完了**
- [x] Refined画面にアイテムが表示されることを確認 → **手動確認完了**
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket.
- [x] Update docs/architecture/*.md
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## 実装サマリー

**Option A（フロントエンドをバックエンドに合わせる）を採用**

### 変更内容

1. **`frontend/src/api/types.ts`**: `IssueType`型を新規定義（Single Source of Truth）
2. **`frontend/src/utils/colors.ts`**: `IssueType`を`api/types.ts`からimport、色マッピング更新
3. **`frontend/src/pages/IssuesPage.tsx`**: フィルターオプションを更新、型安全性向上
4. **`frontend/src/api/hooks/useIssues.ts`**: `issueType`パラメータを`IssueType`型に変更
5. **`frontend/src/mocks/handlers.ts`**: モックデータを更新（4件に増加）
6. **`frontend/src/__tests__/terms-workflow.test.tsx`**: テストを新スキーマに対応
7. **`docs/architecture/frontend.md`**: ドキュメント更新

### Issue Type マッピング

| バックエンド | フロントエンド（修正後） | 色 |
|---|---|---|
| `unclear` | `unclear` | orange |
| `contradiction` | `contradiction` | grape |
| `missing_relation` | `missing_relation` | cyan |
| `unnecessary` | `unnecessary` | gray |

### コミット履歴

```
dd0e8e7 Update frontend.md with correct IssueType values
fb50ccf Fix type safety for IssueType in hooks and components
67d8965 Centralize IssueType definition in api/types.ts
2750352 Implement Issue Type schema alignment with backend
21a5272 Add tests for backend Issue Type schema
```

## Notes

- 現在Issuesテーブルが空のため、この問題はすぐには顕在化しない
- `llm-fewshot-contamination`チケットの修正後、Issuesが正しく生成されるようになった際に問題が発生する
