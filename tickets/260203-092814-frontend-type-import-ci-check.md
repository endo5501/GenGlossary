---
priority: 1
tags: [frontend, dx, ci]
description: "フロントエンドのTypeScriptビルドエラーを事前に検出する仕組みを追加"
created_at: "2026-02-03T09:28:14Z"
started_at: null  # Do not modify manually
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

## 提案する解決策

### 1. Pre-commit フックでビルドチェック
- `pnpm run build` をコミット前に実行
- TypeScriptエラーがあればコミットを拒否

### 2. package.json に typecheck スクリプト追加
```json
{
  "scripts": {
    "typecheck": "tsc --noEmit"
  }
}
```

### 3. Vite開発サーバーのエラーオーバーレイ確認
- Viteのエラーオーバーレイが正しく動作しているか確認
- 必要に応じてプラグイン設定を調整

### 4. React Error Boundary の改善（オプション）
- アプリケーション全体をError Boundaryでラップ
- ビルドエラー時にも有用なエラーメッセージを表示

## Tasks

### 実装タスク
- [ ] `package.json` に `typecheck` スクリプトを追加
- [ ] pre-commit フックの設定（husky または lefthook）
  - `pnpm run typecheck` をpre-commitで実行
- [ ] Viteのエラーオーバーレイ設定を確認・調整
- [ ] 開発ガイドに型インポートのルールを明記

### オプションタスク
- [ ] ESLintルールで型インポートを強制（`@typescript-eslint/consistent-type-imports`）
- [ ] React Error Boundaryの追加

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
