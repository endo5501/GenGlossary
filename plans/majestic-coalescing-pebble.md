# GUI修正チケット化計画

## 調査結果サマリー

plan-gui-fix.md の問題点と plan-gui.md の仕様を照合した結果、以下の修正が必要です。

---

## 問題点の詳細分析

### 問題1: プロジェクト一覧（ホーム）画面の仕様差異

**仕様 (plan-gui.md)**:
- 左：プロジェクト一覧（名前 / 最終更新 / ドキュメント数 / 用語数 / issues数）
- 一番下部に[新規作成]ボタン
- 右：選択プロジェクトの概要カード
  - 入力パス（target_docs相当）
  - LLM設定（provider/model）
  - 最終生成日時
  - ボタン：開く / 複製 / 削除

**現在の実装 (HomePage.tsx)**:
- 左：プロジェクト一覧（Name / Status / Last Run）← **ドキュメント数・用語数・issues数が不足**
- [新規作成]ボタンはヘッダーにある ← **一番下部にない**
- 右：概要カード（Document Root, LLM Provider, LLM Model, Last Run, ボタン）← **ほぼ仕様通り**

---

### 問題2: Create画面の問題

**2-1. Document Root をユーザに入力させている**
- ファイル: `CreateProjectDialog.tsx` L71-78
- 仕様では Document Root 入力は記載なし
- `./projects/` 以下に自動生成すべき

**2-2. LLM Provider がテキスト入力**
- ファイル: `CreateProjectDialog.tsx` L80-85
- SettingsPage では Select コンポーネントを使用済み
- ドロップダウン（ollama / openai）にすべき

**2-3. OpenAI 選択時の URL 設定がない**
- SettingsPage では条件付き表示で実装済み (L185-193)
- Create 画面にも同様の機能が必要

---

### 問題3: 各ページが表示されない（重大）

**症状**: プロジェクトを開いた後、Files/Terms/Provisional/Issues/Refined/Settings をクリックすると「This page will be implemented in a future ticket.」と表示される

**根本原因の可能性**:
1. LeftNavRail のナビゲーションが `/projects/{id}/files` ではなく `/files` に遷移している
2. ルーティング設定の問題
3. `useLocation()` や `extractProjectId()` の動作不良

**関連ファイル**:
- `frontend/src/components/layout/LeftNavRail.tsx` - ナビゲーションロジック
- `frontend/src/routes/index.tsx` - ルーティング設定
- `frontend/src/components/layout/AppShell.tsx` - レイアウト

**各ページの実装状況**:
| ページ | コード実装 | 表示状態 |
|--------|-----------|----------|
| FilesPage | ✅ 完全実装 | ❌ PagePlaceholder表示 |
| TermsPage | ✅ 完全実装 | ❌ PagePlaceholder表示 |
| ProvisionalPage | ✅ 完全実装 | ❌ PagePlaceholder表示 |
| IssuesPage | ✅ 完全実装 | ❌ PagePlaceholder表示 |
| RefinedPage | ✅ 完全実装 | ❌ PagePlaceholder表示 |
| SettingsPage | ✅ 完全実装 | ❌ PagePlaceholder表示 |
| DocumentViewerPage | ❌ スケルトンのみ | ❌ PagePlaceholder表示 |

---

### 問題4: プロジェクト一覧に戻れない

**仕様**: 各プロジェクト詳細画面には「戻る」ボタンがあり、それを押すとプロジェクト一覧（ホーム）へ戻る

**現在の実装**:
- `GlobalTopBar.tsx` のタイトル「GenGlossary」はクリック不可
- `LeftNavRail.tsx` にホームへのリンクがない
- 「戻る」ボタンがない

---

### 問題5: Document Viewer がスケルトン実装

**現在の実装 (DocumentViewerPage.tsx)**:
```tsx
<Text c="dimmed">
  Document content will be displayed here for file ID: {fileId}
</Text>
```

**仕様 (plan-gui.md L118-128)**:
- 左: 原文（タブで文書選択、クリックで用語選択）
- 右: 用語カード（定義、出現箇所一覧、除外/編集/ジャンプボタン）

---

## チケット一覧

### チケット1: ナビゲーション/ルーティング修正（最優先・重大）
**優先度**: 最高
**概要**: プロジェクトを開いた後、各ページが正しく表示されるよう修正
**作業内容**:
1. LeftNavRailのナビゲーションロジックをデバッグ
2. `/projects/{id}/files` 等のルートが正しく動作することを確認
3. `extractProjectId()` と `getPath()` の動作確認
4. 必要に応じてルーティング設定を修正
**修正ファイル**:
- `frontend/src/components/layout/LeftNavRail.tsx`
- `frontend/src/routes/index.tsx`
- `frontend/src/components/layout/AppShell.tsx`

---

### チケット2: プロジェクト詳細画面に「戻る」ボタン追加
**優先度**: 高
**概要**: プロジェクト詳細画面からホーム（プロジェクト一覧）に戻れるようにする
**作業内容**:
1. GlobalTopBarに「戻る」ボタンまたはホームリンクを追加
2. タイトル「GenGlossary」をクリック可能にする（オプション）
3. プロジェクト選択時のみ戻るボタンを表示
**修正ファイル**:
- `frontend/src/components/layout/GlobalTopBar.tsx`

---

### チケット3: プロジェクト未選択時のサイドバー非表示
**優先度**: 高
**概要**: ホーム画面（projectIdなし）ではLeftNavRailを非表示にする
**作業内容**:
1. AppShellでprojectIdの有無を判定
2. projectIdがない場合はNavbarを非表示
**修正ファイル**:
- `frontend/src/components/layout/AppShell.tsx`

---

### チケット4: Create画面 - LLM Provider ドロップダウン化
**優先度**: 高
**概要**: TextInput を Select に変更、ollama/openai の選択肢
**修正ファイル**:
- `frontend/src/components/dialogs/CreateProjectDialog.tsx`

---

### チケット5: Create画面 - OpenAI設定フィールド追加
**優先度**: 高
**概要**: provider=openai の時に base_url 入力欄を条件表示
**修正ファイル**:
- `frontend/src/components/dialogs/CreateProjectDialog.tsx`

---

### チケット6: Create画面 - Document Root 自動化
**優先度**: 中
**概要**: Document Root 入力欄を削除、バックエンドで自動生成
**作業内容**:
1. フロントエンドからDocument Root入力欄を削除
2. バックエンドでプロジェクト作成時に `./projects/{project_name}/` を自動生成
3. APIスキーマからdoc_rootを任意フィールドに変更
**修正ファイル**:
- `frontend/src/components/dialogs/CreateProjectDialog.tsx`
- `src/genglossary/api/routers/projects.py`
- `src/genglossary/api/schemas/project_schemas.py`

---

### チケット7: プロジェクト一覧画面（ホーム）の仕様準拠
**優先度**: 高（2番目）
**概要**: ホーム画面（プロジェクト一覧）をplan-gui.mdの仕様に完全準拠させる

**仕様 (plan-gui.md)**:
```
┌─────────────────────────────────────────────────────────────┐
│                         ホーム画面                           │
├────────────────────────────┬────────────────────────────────┤
│    【左ペイン】              │    【右ペイン】                 │
│    プロジェクト一覧          │    選択プロジェクトの概要カード   │
│                            │                                │
│  ┌─────┬────┬───┬───┬───┐  │  ・入力パス（target_docs相当） │
│  │名前 │更新│Doc│用語│iss│  │  ・LLM設定（provider/model）  │
│  ├─────┼────┼───┼───┼───┤  │  ・最終生成日時               │
│  │Proj1│... │ 5 │ 20│ 3 │  │                                │
│  │Proj2│... │ 3 │ 15│ 0 │  │  [開く] [複製] [削除]          │
│  └─────┴────┴───┴───┴───┘  │                                │
│                            │                                │
│       [新規作成]            │                                │
│       (一覧の下部)          │                                │
└────────────────────────────┴────────────────────────────────┘
```

**現状の実装 (HomePage.tsx)**:
- 左ペイン: Name / Status / Last Run のみ ← **ドキュメント数・用語数・issues数が不足**
- 右ペイン: 概要カード + [Open]/[Clone]/[Delete]ボタン ← **ほぼ仕様通り**
- [新規作成]ボタン: ヘッダーにある ← **一覧の下部にあるべき**

**作業内容**:
1. **左ペイン（プロジェクト一覧）の修正**:
   - カラムを変更: Name/Status/Last Run → 名前/最終更新/ドキュメント数/用語数/issues数
   - [新規作成]ボタンを一覧の下部に移動
2. **右ペイン（概要カード）の確認**:
   - 入力パス、LLM設定、最終生成日時の表示 ← 既存実装でほぼOK
   - [開く]/[複製]/[削除]ボタン ← 既存実装でOK
3. **バックエンドAPI拡張**:
   - プロジェクト一覧APIに統計情報（ドキュメント数、用語数、issues数）を含める

**修正ファイル**:
- `frontend/src/pages/HomePage.tsx`
- `src/genglossary/api/routers/projects.py` (統計情報を含めるよう拡張)
- `src/genglossary/api/schemas/project_schemas.py`

---

### チケット8: Document Viewer 完全実装
**優先度**: 低（最も工数大）
**概要**:
- 左ペイン: ドキュメント原文表示（タブで選択）
- 右ペイン: 用語カード（定義・出現箇所）
- 用語クリックでハイライト
**修正ファイル**:
- `frontend/src/pages/DocumentViewerPage.tsx`
- 必要に応じてバックエンドAPI追加

---

## 推奨実施順序

1. **チケット1 (ナビゲーション/ルーティング修正)** - 最優先、これが解決しないと他の確認ができない
2. **チケット7 (プロジェクト一覧画面の仕様準拠)** - ホーム画面の左右ペイン構成を仕様に合わせる
3. チケット2 (戻るボタン追加)
4. チケット3 (サイドバー非表示)
5. チケット4 (LLM Provider)
6. チケット5 (OpenAI設定)
7. チケット6 (Document Root)
8. チケット8 (Document Viewer)

---

## 検証方法

```bash
# フロントエンド起動
cd frontend && npm run dev

# バックエンド起動
uv run genglossary api serve --reload

# 確認項目
# 1. プロジェクトを開いた後、Files/Terms等のページが正しく表示されるか
# 2. 「戻る」ボタンでホームに戻れるか
# 3. ホーム画面でサイドバーが非表示か
# 4. Create画面でLLM Providerがドロップダウンか
# 5. openai選択時にbase_url入力欄が表示されるか
# 6. プロジェクト作成時にDocument Root入力が不要か
# 7. プロジェクト一覧にドキュメント数・用語数・issues数が表示されるか
# 8. 新規作成ボタンが一覧の下部にあるか
# 9. DocumentViewerでドキュメントが表示されるか
```
