# ホーム画面とプロジェクト詳細画面のレイアウト分離計画

## 問題点

現在のAppShellは全ルートで同一レイアウトを使用しており、ホーム画面（プロジェクト一覧）でも以下が表示されてしまう：
- 左サイドバー（Files, Terms, Provisional等）
- ヘッダーのRun/Stop/Pipelineボタン
- 下部のLogsパネル

## あるべき姿

### ホーム画面（`/`）
```
┌─────────────────────────────────────────────────────────────┐
│  GenGlossary                                                 │
├────────────────────────────┬────────────────────────────────┤
│  プロジェクト一覧テーブル    │  選択プロジェクトの概要カード   │
│  ┌─────┬────┬───┬───┬───┐  │  ・入力パス                    │
│  │名前 │更新│Doc│用語│iss│  │  ・LLM設定                     │
│  └─────┴────┴───┴───┴───┘  │  ・最終生成日時                 │
│       [新規作成]            │  [開く] [複製] [削除]           │
└────────────────────────────┴────────────────────────────────┘
```
- サイドバー: **非表示**
- Run/Stop/Pipeline: **非表示**
- Logsパネル: **非表示**

### プロジェクト詳細画面（`/projects/:id/*`）
```
┌─────────────────────────────────────────────────────────────┐
│  GenGlossary  [RUNNING]        [Run] [Stop] [Full Pipeline] │
├────────────┬────────────────────────────────────────────────┤
│  Files     │  (各ページのコンテンツ)                         │
│  Terms     │                                                │
│  Provisional│                                               │
│  Issues    │                                                │
│  Refined   ├────────────────────────────────────────────────┤
│  Doc Viewer│  Logs                                          │
│  Settings  │  [ログ出力]                                     │
└────────────┴────────────────────────────────────────────────┘
```
- サイドバー: **表示**
- Run/Stop/Pipeline: **表示**
- Logsパネル: **表示**

## 修正方針

**アプローチ: 条件付きレンダリング（projectIdの有無で切り替え）**

既存のAppShellコンポーネント内で`projectId`の有無に基づいてレイアウトを切り替える。

## 修正対象ファイル

### 1. `src/components/layout/AppShell.tsx`
- `projectId`がない場合、`navbar`プロパティを省略（サイドバー非表示）
- `projectId`がない場合、LogPanelをレンダリングしない

### 2. `src/components/layout/GlobalTopBar.tsx`
- `projectId`がない場合、Run/Stop/Pipelineボタンを非表示
- ホーム画面用のシンプルなヘッダー表示（プロジェクト名とステータスも非表示）

### 3. `src/pages/HomePage.tsx`（確認のみ）
- プロジェクト選択時の概要カード（右ペイン）が正しく表示されることを確認

## 実装詳細

### AppShell.tsx の変更

```tsx
// Before
<MantineAppShell
  header={{ height: 60 }}
  navbar={{ width: 200, breakpoint: 'sm' }}
  padding="md"
>

// After
<MantineAppShell
  header={{ height: 60 }}
  navbar={projectId ? { width: 200, breakpoint: 'sm' } : undefined}
  padding="md"
>
  ...
  {projectId && (
    <MantineAppShell.Navbar p="xs">
      <LeftNavRail />
    </MantineAppShell.Navbar>
  )}
  ...
  <MantineAppShell.Main>
    <Box ...>
      <Outlet />
      {projectId && <LogPanel projectId={projectId} runId={runId} />}
    </Box>
  </MantineAppShell.Main>
```

### GlobalTopBar.tsx の変更

```tsx
// projectIdがない場合、シンプルなヘッダー
if (!projectId) {
  return (
    <Group h="100%" px="md" justify="space-between">
      <Group>
        <Title order={3}>GenGlossary</Title>
      </Group>
    </Group>
  )
}

// projectIdがある場合、フルヘッダー（現在のまま）
```

## 検証方法

1. `pnpm dev`でフロントエンドを起動
2. `/`（ホーム画面）にアクセス
   - サイドバーが非表示であること
   - Run/Stop/Pipelineが非表示であること
   - Logsパネルが非表示であること
   - プロジェクト選択時に概要カードが表示されること
3. プロジェクトの[開く]をクリックして`/projects/:id/files`に遷移
   - サイドバーが表示されること
   - Run/Stop/Pipelineが表示されること
   - Logsパネルが表示されること
4. `pnpm test`でテストがパスすること

## テスト更新

`src/__tests__/app-shell.test.tsx`のテストを更新して、条件付きレンダリングを検証する。
