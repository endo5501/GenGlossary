# Settings ページ実装計画

## 概要

左サイドバーからアクセスできる Settings ページを実装し、プロジェクト名と LLM 設定（provider, model, base_url）を変更可能にする。

## 現状分析

### バックエンド
- `ProjectUpdateRequest` は現在 `llm_provider` と `llm_model` のみサポート
- `name` の更新機能が**未実装** → 追加が必要
- `llm_base_url` フィールドが**未実装** → モデル・スキーマ・DBに追加が必要
- DBスキーマバージョンは 1（マイグレーションが必要）

### フロントエンド
- Settings は既にサイドバーに登録済み（`/settings` プレースホルダー）
- 他のページは project-scoped (`/projects/$projectId/files`) パターンを使用
- Toast 通知用の `@mantine/notifications` が**未インストール**

## 設計方針

1. **Settings をプロジェクトスコープに**: `/projects/$projectId/settings`
2. **バックエンド先行**: name 更新 API と llm_base_url を先に実装
3. **TDD 厳守**: テストファースト開発
4. **DBマイグレーション**: スキーマバージョン 1 → 2 への移行

---

## 実装ステップ

### Phase 1: バックエンド変更 (llm_base_url 追加)

#### Step 1.0: モデル・スキーマ・DBに llm_base_url 追加 (TDD)

**テストファイル**: `tests/models/test_project.py`, `tests/db/test_project_repository.py`

追加するテストケース:
- `test_project_has_llm_base_url_field` - モデルにフィールドがある
- `test_create_project_with_llm_base_url` - base_url 付きでプロジェクト作成
- `test_update_llm_base_url` - base_url の更新

**ファイル**: `src/genglossary/models/project.py`

```python
class Project(BaseModel):
    # ... 既存フィールド ...
    llm_base_url: str = ""  # 追加（デフォルト空文字）
```

**ファイル**: `src/genglossary/db/registry_schema.py`

スキーマバージョン 2 へのマイグレーション追加:
```python
REGISTRY_SCHEMA_VERSION = 2

# マイグレーション関数追加
def migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """Add llm_base_url column to projects table."""
    conn.execute(
        "ALTER TABLE projects ADD COLUMN llm_base_url TEXT NOT NULL DEFAULT ''"
    )
```

**ファイル**: `src/genglossary/api/schemas/project_schemas.py`

`ProjectResponse` と `ProjectCreateRequest` に `llm_base_url` 追加

### Phase 2: バックエンド変更 (name + llm_base_url 更新)

#### Step 2.1: バックエンドテスト追加 (RED)

**ファイル**: `tests/api/routers/test_projects.py`

追加するテストケース:
- `test_updates_name` - プロジェクト名の更新成功
- `test_returns_409_for_duplicate_name_on_update` - 重複名でのエラー
- `test_returns_422_for_empty_name_on_update` - 空文字でのバリデーションエラー
- `test_updates_llm_base_url` - base_url の更新成功

#### Step 2.2: スキーマ更新 (GREEN)

**ファイル**: `src/genglossary/api/schemas/project_schemas.py`

```python
class ProjectUpdateRequest(BaseModel):
    """Request schema for updating a project."""

    name: str | None = Field(None, description="New project name")
    llm_provider: str | None = Field(None, description="New LLM provider name")
    llm_model: str | None = Field(None, description="New LLM model name")
    llm_base_url: str | None = Field(None, description="New LLM base URL")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate project name if provided."""
        if v is None:
            return None
        return _validate_project_name(v)
```

#### Step 2.3: リポジトリ更新

**ファイル**: `src/genglossary/db/project_repository.py`

`update_project` 関数に `name` と `llm_base_url` パラメータを追加:
```python
def update_project(
    conn: sqlite3.Connection,
    project_id: int,
    name: str | None = None,  # 追加
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_base_url: str | None = None,  # 追加
    ...
) -> None:
```

#### Step 2.4: API ルーター更新

**ファイル**: `src/genglossary/api/routers/projects.py`

`update_existing_project` エンドポイントで:
- 名前の重複チェック（409 エラー）
- `name` と `llm_base_url` を `update_project` に渡す

---

### Phase 3: フロントエンド変更

#### Step 3.1: 依存関係インストール

```bash
cd frontend && npm install @mantine/notifications
```

#### Step 3.2: Notifications プロバイダー設定

**ファイル**: `frontend/src/main.tsx`

```tsx
import { Notifications } from '@mantine/notifications'
import '@mantine/notifications/styles.css'

// MantineProvider 内に追加
<Notifications />
```

#### Step 3.3: フロントエンドテスト追加 (RED)

**ファイル**: `frontend/src/__tests__/settings-page.test.tsx`

テストケース:
1. ローディング状態の表示
2. プロジェクト設定の表示
3. 空文字でのバリデーションエラー
4. 重複名での 409 エラー表示
5. 正常な保存と成功トースト
6. LLM プロバイダー選択
7. LLM モデル入力
8. **Base URL の表示/非表示（OpenAI 選択時のみ表示）**
9. **Base URL の更新**
10. 変更がない場合は保存ボタン無効化

#### Step 3.4: API 型定義更新

**ファイル**: `frontend/src/api/types.ts`

```typescript
export interface ProjectResponse {
  // ... 既存フィールド ...
  llm_base_url: string  // 追加
}

export interface ProjectUpdateRequest {
  name?: string
  llm_provider?: string
  llm_model?: string
  llm_base_url?: string  // 追加
}
```

#### Step 3.5: モックハンドラー更新

**ファイル**: `frontend/src/mocks/handlers.ts`

PATCH ハンドラーで name, llm_base_url 更新をサポート、重複時は 409 を返す

#### Step 3.6: SettingsPage コンポーネント作成 (GREEN)

**ファイル**: `frontend/src/pages/SettingsPage.tsx`

```tsx
interface SettingsPageProps {
  projectId: number
}

export function SettingsPage({ projectId }: SettingsPageProps) {
  // useProject フックでプロジェクトデータ取得
  // フォーム状態管理 (useState)
  // 変更検知 (useMemo)
  // バリデーション関数
  // 保存ハンドラー (mutation + notifications)

  // フォーム要素:
  // - TextInput: プロジェクト名
  // - Select: LLM プロバイダー (ollama / openai)
  // - TextInput: モデル名
  // - TextInput: Base URL（OpenAI 選択時のみ表示）
  // - Button: 保存
}
```

#### Step 3.7: ルーティング追加

**ファイル**: `frontend/src/routes/index.tsx`

```tsx
const projectSettingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId/settings',
  component: () => {
    const { projectId } = projectSettingsRoute.useParams()
    return <SettingsPage projectId={Number(projectId)} />
  },
})

// routeTree に追加
```

#### Step 3.8: エクスポート追加

**ファイル**: `frontend/src/pages/index.ts`

```typescript
export { SettingsPage } from './SettingsPage'
```

#### Step 3.9: サイドバーをプロジェクトコンテキスト対応に

**ファイル**: `frontend/src/components/layout/LeftNavRail.tsx`

```tsx
interface LeftNavRailProps {
  projectId?: number
}

// navItems を動的に生成
const getNavItems = (projectId?: number): NavItem[] => [
  {
    label: 'Files',
    icon: IconFiles,
    path: projectId ? `/projects/${projectId}/files` : '/files'
  },
  // ... 他のアイテムも同様
  {
    label: 'Settings',
    icon: IconSettings,
    path: projectId ? `/projects/${projectId}/settings` : '/settings'
  },
]
```

**ファイル**: `frontend/src/components/layout/AppShell.tsx`

`LeftNavRail` に `projectId` を渡すように更新

---

## 変更ファイル一覧

### バックエンド
| ファイル | 変更内容 |
|---------|---------|
| `tests/models/test_project.py` | llm_base_url フィールドテスト追加 |
| `tests/db/test_project_repository.py` | llm_base_url 関連テスト追加 |
| `tests/api/routers/test_projects.py` | name, llm_base_url 更新テスト追加 |
| `src/genglossary/models/project.py` | `llm_base_url` フィールド追加 |
| `src/genglossary/db/registry_schema.py` | スキーマ v2 マイグレーション追加 |
| `src/genglossary/db/project_repository.py` | `llm_base_url` 対応、`update_project` に `name` パラメータ追加 |
| `src/genglossary/api/schemas/project_schemas.py` | `ProjectUpdateRequest` に `name`, `llm_base_url` 追加 |
| `src/genglossary/api/routers/projects.py` | name 更新処理と重複チェック |

### フロントエンド
| ファイル | 変更内容 |
|---------|---------|
| `frontend/package.json` | `@mantine/notifications` 追加 |
| `frontend/src/main.tsx` | Notifications プロバイダー追加 |
| `frontend/src/__tests__/settings-page.test.tsx` | 新規テストファイル |
| `frontend/src/api/types.ts` | `ProjectResponse`, `ProjectUpdateRequest` に `llm_base_url` 追加 |
| `frontend/src/mocks/handlers.ts` | PATCH ハンドラー更新 (name, llm_base_url) |
| `frontend/src/pages/SettingsPage.tsx` | 新規ページコンポーネント |
| `frontend/src/pages/index.ts` | SettingsPage エクスポート |
| `frontend/src/routes/index.tsx` | project-scoped settings ルート追加 |
| `frontend/src/components/layout/LeftNavRail.tsx` | プロジェクトコンテキスト対応 |
| `frontend/src/components/layout/AppShell.tsx` | projectId を LeftNavRail に渡す |

---

## 検証方法

### ユニットテスト
```bash
# バックエンドテスト（全体）
uv run pytest -v

# バックエンドテスト（プロジェクト関連のみ）
uv run pytest tests/api/routers/test_projects.py tests/db/test_project_repository.py tests/models/test_project.py -v

# フロントエンドテスト
cd frontend && npm test
```

### 静的解析
```bash
uv run pyright
```

### E2E 検証
1. GUI サーバー起動: `uv run genglossary gui`
2. ブラウザで http://localhost:8000 にアクセス
3. プロジェクトを作成または選択
4. Settings ページに移動
5. プロジェクト名を変更して保存 → 成功トースト確認
6. LLM プロバイダーを "openai" に変更 → Base URL フィールドが表示される
7. Base URL を入力して保存 → 成功トースト確認
8. LLM プロバイダーを "ollama" に戻す → Base URL フィールドが非表示になる
9. 空文字で保存 → バリデーションエラー確認
10. 既存の名前で保存 → 重複エラー確認
