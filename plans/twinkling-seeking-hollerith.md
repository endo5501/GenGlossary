# GUI機能追加チケットのレビュー

## 分析対象

- **要件定義**: `plan-gui.md`
- **作成済みチケット**: 6件（260124-*.md）

## チケット一覧と概要

| # | ファイル | Priority | 概要 |
|---|----------|----------|------|
| 1 | 260124-164005-gui-backend-scaffold.md | 3 | FastAPIバックエンド基盤 |
| 2 | 260124-164008-gui-project-model-storage.md | 4 | プロジェクトモデル・CRUD |
| 3 | 260124-164011-gui-api-operations-runner.md | 5 | パイプライン操作API・ジョブ管理 |
| 4 | 260124-164013-gui-frontend-scaffold.md | 6 | Reactフロントエンド基盤 |
| 5 | 260124-164016-gui-frontend-projects-files.md | 7 | プロジェクト一覧・Files・Document Viewer |
| 6 | 260124-164019-gui-frontend-terms-review.md | 8 | Terms/Provisional/Issues/Refined画面 |

---

## 要件カバレッジ分析

### ✅ 十分にカバーされている機能

| 画面/機能 | カバーするチケット |
|-----------|-------------------|
| プロジェクト一覧（ホーム） | #2, #5 |
| 新規作成/複製/削除 | #2, #5 |
| グローバル操作バー（実行/停止） | #3, #6 |
| 左サイドバー（ナビ） | #4 |
| Files（登録文書） | #5 |
| Terms（抽出用語） | #6 |
| Provisional（暫定用語集） | #6 |
| Issues（精査結果） | #6 |
| Refined（最終用語集） | #6 |
| Document Viewer | #5 |
| ログビュー | #3, #4, #6 |

### ⚠️ 不足または曖昧な点

#### 1. Settings画面のUI実装

**問題**: `plan-gui.md`で「Settings（設定）」が左サイドバーの一項目として明記されているが、Settings画面のUI実装チケットがない。

**該当箇所**:
```markdown
左サイドバー（ナビ）
- Settings（設定）

Settings はプロジェクト全体の設定を行う画面で、プロジェクト名の変更や使用する LLM 設定の編集を行う。
```

**対応案**: チケット#5または#6に含めるか、新規チケットを追加

---

#### 2. データ取得・更新用APIエンドポイント

**問題**: チケット#3は「パイプライン操作（実行/停止/ログ）」に焦点を当てているが、以下のAPIが明示されていない:

- Terms一覧・詳細・編集・除外・手動追加 API
- Provisional一覧・詳細・編集・除外・再生成 API
- Issues一覧・詳細 API
- Refined一覧・詳細・エクスポート API
- Files一覧・追加・削除・差分スキャン API

**補足**: 既存の `cli_db.py` にこれらの機能があるので、API化は比較的容易。

**対応案**:
- チケット#3の範囲を拡大（推奨）
- または新規チケット「gui-api-data-endpoints」を追加

---

#### 3. Document Viewerの詳細機能

**問題**: `plan-gui.md`のDocument Viewer要件:
```markdown
- クリックで用語選択
- 用語カード（定義、出現箇所一覧、除外/編集/ジャンプボタン）
```

チケット#5では「term card placeholder」とあり、完全な実装範囲が不明確。

**対応案**: チケット#5の詳細を明確化

---

## 決定事項

- **チケット対応**: 新規チケット追加（明確な分離）
- **デザインシステム**: Mantine（React向けUIライブラリ）

---

## 追加する新規チケット

### 新規チケット1: gui-api-data-endpoints

**ファイル名**: `260124-164009-gui-api-data-endpoints.md`
**Priority**: 4（チケット#2の後、#3の前）

**概要**: Terms/Provisional/Issues/Refined/FilesのCRUD APIエンドポイント

**タスク**:
- [ ] **Red**: テスト追加（`tests/api/test_data_endpoints.py`）
- [ ] Terms API: GET /projects/{id}/terms, PATCH, DELETE, POST（手動追加）
- [ ] Provisional API: GET /projects/{id}/provisional, PATCH（定義・confidence編集）, regenerate-single
- [ ] Issues API: GET /projects/{id}/issues（フィルタ対応）
- [ ] Refined API: GET /projects/{id}/refined, GET export-md
- [ ] Files API: GET /projects/{id}/files, POST（追加）, DELETE, POST diff-scan
- [ ] 既存 `cli_db.py` と `*_repository.py` のロジック再利用
- [ ] **Green**: テスト通過確認

**依存関係**: チケット#1, #2完了後に着手

---

### 新規チケット2: gui-frontend-settings

**ファイル名**: `260124-164017-gui-frontend-settings.md`
**Priority**: 7.5（チケット#5の後、#6の前）

**概要**: Settings画面のUI実装

**タスク**:
- [ ] **Red**: テスト追加（`frontend/src/__tests__/settings-page.test.tsx`）
- [ ] Settings画面のルーティング追加（左サイドバーからアクセス）
- [ ] プロジェクト名変更フォーム
- [ ] LLM設定編集フォーム（provider/model選択）
- [ ] 保存ボタンとAPI連携
- [ ] バリデーションとエラー表示
- [ ] **Green**: テスト通過確認

**依存関係**: チケット#4, #5完了後に着手

---

## 更新後のチケット一覧（実行順）

| 順序 | ファイル | Priority | 概要 |
|------|----------|----------|------|
| 1 | 260124-164005-gui-backend-scaffold.md | 3 | FastAPIバックエンド基盤 |
| 2 | 260124-164008-gui-project-model-storage.md | 4 | プロジェクトモデル・CRUD |
| **3** | **260124-164009-gui-api-data-endpoints.md** | **4.5** | **データCRUD API（新規）** |
| 4 | 260124-164011-gui-api-operations-runner.md | 5 | パイプライン操作・ジョブ管理 |
| 5 | 260124-164013-gui-frontend-scaffold.md | 6 | Reactフロントエンド基盤（Mantine） |
| 6 | 260124-164016-gui-frontend-projects-files.md | 7 | プロジェクト一覧・Files・DocViewer |
| **7** | **260124-164017-gui-frontend-settings.md** | **7.5** | **Settings画面（新規）** |
| 8 | 260124-164019-gui-frontend-terms-review.md | 8 | Terms/Provisional/Issues/Refined画面 |

---

## 既存チケットへの更新

### チケット#4 (gui-frontend-scaffold) の更新

デザインシステムをMantineに確定：
```markdown
- [ ] Choose and configure Mantine as design system with custom theme tokens
```

---

## 実装時の注意点

1. **API設計**: RESTful設計、OpenAPI/Swagger自動生成
2. **既存コード再利用**: `*_repository.py` のロジックをAPI層から呼び出し
3. **フロントエンド**: Mantine + TanStack Router + TanStack Query
4. **認証**: 現時点では認証なし（ローカル実行前提）

---

## 新規チケットのドラフト

### 260124-164009-gui-api-data-endpoints.md

```markdown
---
priority: 4.5
tags: [api, crud, gui]
description: "Expose Terms/Provisional/Issues/Refined/Files data as REST endpoints for GUI consumption."
created_at: "2026-01-25T00:00:00Z"
started_at: null
closed_at: null
---

# Ticket Overview

Provide RESTful API endpoints for all data entities used in the GUI. Leverage existing
repository classes (term_repository, provisional_repository, etc.) to serve CRUD
operations. This bridges the gap between the operations API (run/stop) and the
frontend data needs.

Reference: `plan-gui.md` - Terms/Provisional/Issues/Refined/Files各画面のデータ取得・編集に必要

## Tasks

- [ ] **Red**: テスト追加（`tests/api/test_data_endpoints.py`）— 各エンドポイントのレスポンス検証
- [ ] Terms API
  - GET /api/projects/{project_id}/terms — 一覧取得
  - GET /api/projects/{project_id}/terms/{term_id} — 詳細取得
  - PATCH /api/projects/{project_id}/terms/{term_id} — 編集
  - DELETE /api/projects/{project_id}/terms/{term_id} — 除外
  - POST /api/projects/{project_id}/terms — 手動追加
- [ ] Provisional API
  - GET /api/projects/{project_id}/provisional — 一覧取得
  - PATCH /api/projects/{project_id}/provisional/{entry_id} — 定義・confidence編集
  - POST /api/projects/{project_id}/provisional/{entry_id}/regenerate — 単一再生成
- [ ] Issues API
  - GET /api/projects/{project_id}/issues — 一覧取得（issue_typeフィルタ対応）
- [ ] Refined API
  - GET /api/projects/{project_id}/refined — 一覧取得
  - GET /api/projects/{project_id}/refined/export-md — Markdownエクスポート
- [ ] Files API
  - GET /api/projects/{project_id}/files — 一覧取得
  - POST /api/projects/{project_id}/files — ファイル追加
  - DELETE /api/projects/{project_id}/files/{file_id} — ファイル削除
  - POST /api/projects/{project_id}/files/diff-scan — 差分スキャン
- [ ] 既存repositoryクラスを呼び出すservice層を作成
- [ ] **Green**: テスト通過確認
- [ ] docs/architecture.md更新

## Notes

既存の `cli_db.py` の実装パターンを参考に、repository層を直接呼び出す。
プロジェクトごとのDB分離を考慮した接続管理が必要。
```

---

### 260124-164017-gui-frontend-settings.md

```markdown
---
priority: 7.5
tags: [frontend, gui, settings]
description: "Implement Settings page UI for project configuration (name, LLM settings)."
created_at: "2026-01-25T00:00:00Z"
started_at: null
closed_at: null
---

# Ticket Overview

Build the Settings page accessible from the left sidebar. Allow users to modify
project name and LLM configuration (provider, model). Integrate with the project
update API.

Reference: `plan-gui.md` 「Settings（設定）」セクション

## Tasks

- [ ] **Red**: テスト追加（`frontend/src/__tests__/settings-page.test.tsx`）
- [ ] 左サイドバーにSettingsリンク追加
- [ ] Settings画面のルーティング設定
- [ ] プロジェクト名変更フォーム
  - テキスト入力
  - バリデーション（空文字不可、重複チェック）
- [ ] LLM設定フォーム
  - Provider選択（Ollama / OpenAI Compatible）
  - Model入力
  - ベースURL入力（OpenAI Compatible時）
- [ ] 保存ボタン実装
  - API呼び出し (PATCH /api/projects/{id})
  - 成功/エラートースト表示
- [ ] ローディング状態とエラー状態の表示
- [ ] **Green**: テスト通過確認
- [ ] docs/architecture.md更新

## Notes

Mantineのフォームコンポーネントを使用。react-hook-formまたはMantine formとの
統合を検討。
```
