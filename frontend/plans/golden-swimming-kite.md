# Frontend アーキテクチャドキュメント追加計画

## 概要

frontend/ ブランチで実装した内容を `docs/architecture/` にドキュメント化する。

## 対象ファイル

| ファイル | 操作 | 内容 |
|---------|------|------|
| `docs/architecture/frontend.md` | 新規作成 | フロントエンドアーキテクチャの包括的ドキュメント |
| `docs/architecture/README.md` | 追記 | リンク追加、レイヤー図更新 |
| `docs/architecture/directory-structure.md` | 追記 | フロントエンドディレクトリ構成 |

---

## 1. frontend.md（新規作成）

### 目次構成

```
# フロントエンド層（React SPA）

## 技術スタック
- React 19.2 + TypeScript 5.9 + Vite 7.2
- Mantine v8.3 + Tabler Icons
- TanStack Router / Query

## アプリケーション構造
- main.tsx（エントリーポイント）
- theme/theme.ts（テーマ設定）

## コンポーネント設計
### レイアウトコンポーネント
- AppShell: ヘッダー60px、ナビ200px
- GlobalTopBar: タイトル、ステータス、Run/Stop
- LeftNavRail: 7ページナビ
- LogPanel: 折りたたみログビューア

### 共通コンポーネント
- PagePlaceholder

## APIクライアント
- client.ts: get/post/put/patch/delete, ApiError
- types.ts: FileResponse, TermResponse, RunResponse等
- hooks/: TanStack Queryフック（将来）

## ルーティング
- /, /files, /terms, /provisional, /issues, /refined, /document-viewer, /settings

## テスト戦略
- Vitest + RTL + MSW
- 49テスト（api-client 14, app-shell 19, routing 16）

## 開発コマンド
- pnpm dev / build / test / lint
```

---

## 2. README.md への追記

### ドキュメント一覧テーブルに追加
```markdown
| [フロントエンド](./frontend.md) | React SPA、コンポーネント設計、APIクライアント |
```

### 主要レイヤー図を更新
```
┌─────────────────────────────────────┐
│      フロントエンド層（SPA）        │  ← 追加
│  (React, Mantine, TanStack)         │
├─────────────────────────────────────┤
│          CLI / API 層               │
...
```

---

## 3. directory-structure.md への追記

ファイル末尾に `## フロントエンド（frontend/）` セクションを追加:

```
frontend/
├── src/
│   ├── __tests__/           # テストコード
│   ├── api/                 # API通信層
│   ├── components/          # Reactコンポーネント
│   │   ├── common/
│   │   └── layout/
│   ├── routes/              # ルーティング設定
│   ├── theme/               # テーマ設定
│   └── main.tsx             # エントリーポイント
├── package.json
├── vite.config.ts
└── vitest.config.ts
```

---

## 実装順序

1. `docs/architecture/frontend.md` 新規作成
2. `docs/architecture/README.md` 追記
3. `docs/architecture/directory-structure.md` 追記
4. コミット

---

## 検証方法

- ドキュメント内のリンクが正しく機能するか確認
- マークダウンの構文エラーがないか確認
- 既存ドキュメントとの整合性確認
