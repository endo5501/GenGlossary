---
priority: 1
tags: [frontend, dx, ci]
description: "フロントエンドのTypeScriptビルドエラーを事前に検出する仕組みを追加"
created_at: "2026-02-03T09:28:14Z"
started_at: 2026-02-04T15:24:22Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# フロントエンドビルドエラー早期検出の仕組み追加

## 背景（インシデント報告）

### 発生した問題
2026-02-03に以下の問題が発生：
1. フロントエンドで型インポートエラーが混入
2. 開発サーバー起動中にビルドエラーが発生
3. 画面が真っ白になり、何も表示されなくなった
4. サーバー再起動でも問題は解決せず

### 原因
```typescript
// エラーになったコード
import { Select, TextInput, Alert, Loader, ComboboxProps } from '@mantine/core'

// 正しいコード（type キーワードが必要）
import { Select, TextInput, Alert, Loader, type ComboboxProps } from '@mantine/core'
```

`tsconfig.json` で `verbatimModuleSyntax: true` が設定されているため、型のインポートには `type` キーワードが必須。

### 問題点
1. **Vite開発サーバー**: TypeScriptエラーがあっても起動するが、画面が真っ白になる
2. **エラーが分かりにくい**: ブラウザコンソールを見ないとエラーに気づけない
3. **ビルドチェックがない**: コミット前にビルドを確認するフックがない

## 採用する解決策

### 概要

Husky を使った pre-commit フックで `tsc --noEmit` を実行し、型エラーがあればコミットを拒否する。

### 変更するファイル

| ファイル | 変更内容 |
|---------|---------|
| `frontend/package.json` | `typecheck` スクリプト追加 |
| `frontend/.husky/pre-commit` | 新規作成（huskyフック） |
| `frontend/package.json` | `prepare` スクリプト追加（husky初期化用） |

### 実行フロー

```
git commit 実行
    ↓
.husky/pre-commit が起動
    ↓
cd frontend && pnpm run typecheck
    ↓
tsc -b --noEmit 実行
    ↓
エラーあり → コミット拒否
エラーなし → コミット成功
```

### 追加するスクリプト

```json
{
  "scripts": {
    "typecheck": "tsc -b --noEmit",
    "prepare": "cd .. && husky frontend/.husky"
  }
}
```

`tsc -b` はプロジェクト参照（tsconfig.json の references）を考慮してビルドする。

### スコープ外（今回やらないこと）

- ESLint ルール追加
- Vite エラーオーバーレイ改善
- React Error Boundary
- 開発ガイドへの記載（必要なら別チケット）

## Tasks

### 実装タスク
- [ ] `frontend/package.json` に `typecheck` スクリプト追加
- [ ] Husky をインストール・初期化
- [ ] `.husky/pre-commit` を編集
- [ ] 動作確認（型エラーありでコミット拒否されることを確認）

### 完了条件
- [ ] `pnpm run typecheck` が正常に動作する
- [ ] 型エラーがあるとコミットが拒否される
- [ ] 型エラーがないとコミットが成功する

### 品質タスク
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

### 関連ファイル
- `frontend/tsconfig.json` - `verbatimModuleSyntax: true` の設定
- `frontend/package.json` - スクリプト追加先
- `frontend/src/components/inputs/LlmSettingsForm.tsx` - 今回の修正箇所

### 参考リンク
- [TypeScript verbatimModuleSyntax](https://www.typescriptlang.org/tsconfig#verbatimModuleSyntax)
- [@typescript-eslint/consistent-type-imports](https://typescript-eslint.io/rules/consistent-type-imports/)

### 今回の修正コミット
- `ab2b64e` - Fix type import for ComboboxProps in LlmSettingsForm
