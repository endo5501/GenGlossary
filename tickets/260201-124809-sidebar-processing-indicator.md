---
priority: 3
tags: [ux, frontend]
description: "左サイドバーの各メニューに処理中インジケーターを追加し、現在のシーケンスを可視化"
created_at: "2026-02-01T12:48:09Z"
started_at: 2026-02-02T14:12:04Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# サイドバー処理中インジケーター

## 概要

左サイドバーの各選択メニューのボタンに、処理中であることを示すマーク（アイコンや点滅など）を追加し、
現在どのシーケンス（ステップ）を実行しているかをわかりやすくする。

## 現状の問題

- パイプライン実行中、どのステップを処理しているかが視覚的にわからない
- ユーザーは処理の進捗を把握しづらい

## 期待する動作

- 処理中のステップに対応するサイドバーメニューに、視覚的なインジケーターを表示
  - 例: スピナーアイコン、点滅エフェクト、バッジなど
- 処理が完了したらインジケーターを消す、または完了マークに変更

## 対象メニュー項目

1. Files
2. Terms
3. Provisional
4. Issues
5. Refined
6. Document Viewer

## Tasks

- [ ] 現在の処理ステップを追跡する状態管理の実装
- [ ] サイドバーメニューへのインジケーターUI追加
- [ ] 処理開始/完了時のインジケーター更新ロジック
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

- パイプラインの各ステップとサイドバーメニューの対応関係を明確にする
- アクセシビリティ（視覚障害者向け）も考慮する

---

## 設計

### データフローと状態管理

**既存のデータフロー活用:**
- `useCurrentRun` フックが `RunResponse` を返す（`current_step` 含む）
- 2秒ごとにポーリング済み → 新しい状態管理は不要

**ステップとメニューのマッピング:**
```typescript
const STEP_TO_MENU: Record<string, string> = {
  extract: '/terms',
  provisional: '/provisional',
  issues: '/issues',
  refined: '/refined',
}
```

### UI実装

**スピナーコンポーネント:**
- Mantine の `Loader` コンポーネントを使用（サイズ: 20px、既存アイコンと同じ）
- `leftSection` にアイコンの代わりにスピナーを表示

**LeftNavRail の変更:**
```tsx
const isProcessing = (basePath: string) => {
  if (run?.status !== 'running' || !run.current_step) return false
  return STEP_TO_MENU[run.current_step] === basePath
}

leftSection={
  isProcessing(item.basePath)
    ? <Loader size={20} />
    : <item.icon size={20} />
}
```

**アクセシビリティ:**
- `aria-busy="true"` を処理中の NavLink に追加

### バックエンド修正

**変更箇所:** `src/genglossary/runs/executor.py` の `_do_review` メソッド

レビューステップでも `_create_progress_callback` を使用し、`step_name = "issues"` を設定。

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/genglossary/runs/executor.py` | レビューステップに `current_step = "issues"` を設定 |
| `frontend/src/components/layout/LeftNavRail.tsx` | スピナー表示ロジック追加 |

### テスト方針

1. **バックエンド:** `_do_review` がプログレスコールバックを呼ぶことを確認
2. **フロントエンド:** `LeftNavRail` のユニットテスト追加（各 `current_step` パターン）
