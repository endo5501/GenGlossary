# コード簡略化リファクタリング計画

## 概要

code-simplifier エージェントによるレビュー指摘に基づき、重複コードの排除と可読性向上のリファクタリングを行う。

---

## 修正対象（7件）

| # | 優先度 | 問題 | ファイル |
|---|--------|------|----------|
| 1 | 高 | バリデーション関数の重複 | `project_schemas.py` |
| 2 | 高 | プロジェクト取得パターンの重複 | `projects.py` |
| 3 | 高 | DBクリーンアップの重複 | `projects.py` |
| 4 | 高 | DiffScanResults内の繰り返し | `FilesPage.tsx` |
| 5 | 中 | handleClose内の不要なリセット | `CloneProjectDialog.tsx` |
| 6 | 中 | useEffect依存配列の修正 | `CloneProjectDialog.tsx` |
| 7 | 中 | 日付フォーマットの重複 | `HomePage.tsx` |

---

## Step 1: バリデーション関数の共通化

**ファイル**: `src/genglossary/api/schemas/project_schemas.py`

**問題**: `ProjectCreateRequest.validate_name` と `ProjectCloneRequest.validate_name` が同一ロジック

**修正**:
```python
def _validate_project_name(v: str) -> str:
    """Validate project name is not empty."""
    stripped = v.strip()
    if not stripped:
        raise ValueError("Project name cannot be empty")
    return stripped


class ProjectCreateRequest(BaseModel):
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _validate_project_name(v)


class ProjectCloneRequest(BaseModel):
    @field_validator("new_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _validate_project_name(v)
```

---

## Step 2: プロジェクト取得ヘルパー追加

**ファイル**: `src/genglossary/api/routers/projects.py`

**問題**: `get_project` + 404チェックが3箇所で重複

**修正**:
```python
def _get_project_or_404(
    registry_conn: sqlite3.Connection,
    project_id: int,
) -> Project:
    """Get project or raise 404."""
    project = get_project(registry_conn, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project
```

使用箇所:
- `get_project_by_id`
- `delete_existing_project`
- `update_existing_project`

---

## Step 3: DBクリーンアップヘルパー追加

**ファイル**: `src/genglossary/api/routers/projects.py`

**問題**: DBファイル削除ロジックが2箇所で重複

**修正**:
```python
def _cleanup_db_file(db_path: str) -> None:
    """Cleanup orphaned database file."""
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass
```

使用箇所:
- `create_new_project` の except ブロック
- `clone_existing_project` の except ブロック

---

## Step 4: ChangeListコンポーネント抽出

**ファイル**: `frontend/src/pages/FilesPage.tsx`

**問題**: Added/Modified/Deleted セクションがほぼ同一構造で3回繰り返し

**修正**:
```typescript
interface ChangeSectionProps {
  items: string[]
  label: string
  color: string
  prefix: string
}

function ChangeSection({ items, label, color, prefix }: ChangeSectionProps) {
  if (items.length === 0) return null

  return (
    <Box>
      <Group gap="xs" mb="xs">
        <Badge color={color} size="sm">{label}</Badge>
        <Text size="sm" c="dimmed">({items.length} files)</Text>
      </Group>
      <Stack gap={4}>
        {items.map((path) => (
          <Text key={path} size="sm" c={color}>
            {prefix} {path}
          </Text>
        ))}
      </Stack>
    </Box>
  )
}

// DiffScanResults内で使用
const sections = [
  { items: results.added, label: 'Added', color: 'green', prefix: '+' },
  { items: results.modified, label: 'Modified', color: 'yellow', prefix: '~' },
  { items: results.deleted, label: 'Deleted', color: 'red', prefix: '-' },
]

{sections.map((section) => (
  <ChangeSection key={section.label} {...section} />
))}
```

---

## Step 5: handleClose簡略化

**ファイル**: `frontend/src/components/dialogs/CloneProjectDialog.tsx`

**問題**: `handleClose`内の状態リセットは`useEffect`で行われるため不要

**修正**:
```typescript
const handleClose = () => {
  onClose()
}
```

---

## Step 6: useEffect依存配列修正

**ファイル**: `frontend/src/components/dialogs/CloneProjectDialog.tsx`

**問題**: `project.name`を使用しているのに`project.id`を依存配列に指定

**修正**:
```typescript
useEffect(() => {
  if (opened) {
    setNewName(`${project.name} (Copy)`)
    setError(null)
  }
}, [opened, project.name])  // project.id → project.name
```

---

## Step 7: 日付フォーマットユーティリティ追加

**ファイル**: `frontend/src/pages/HomePage.tsx`

**問題**: 日付フォーマットが2箇所で異なる形式（`toLocaleString` vs `toLocaleDateString`）

**修正**:
```typescript
function formatLastRun(lastRunAt: string | null, format: 'short' | 'long' = 'short'): string {
  if (!lastRunAt) return format === 'short' ? '-' : 'Never'
  const date = new Date(lastRunAt)
  return format === 'short' ? date.toLocaleDateString() : date.toLocaleString()
}

// ProjectSummaryCard内
{formatLastRun(project.last_run_at, 'long')}

// Table内
{formatLastRun(project.last_run_at)}
```

---

## 修正対象ファイル一覧

| ファイル | 修正内容 |
|----------|----------|
| `src/genglossary/api/schemas/project_schemas.py` | `_validate_project_name` 共通関数追加 |
| `src/genglossary/api/routers/projects.py` | `_get_project_or_404`, `_cleanup_db_file` 追加 |
| `frontend/src/pages/FilesPage.tsx` | `ChangeSection` コンポーネント抽出 |
| `frontend/src/components/dialogs/CloneProjectDialog.tsx` | handleClose簡略化、依存配列修正 |
| `frontend/src/pages/HomePage.tsx` | `formatLastRun` ユーティリティ追加 |

---

## 検証方法

1. **バックエンドテスト**: `uv run pytest tests/api/routers/test_projects.py -v`
2. **静的解析**: `uv run pyright src/genglossary/api/`
3. **フロントエンドテスト**: `cd frontend && npm run test`
4. **ビルド確認**: `cd frontend && npm run build`
5. **手動確認**: 既存機能が正常に動作すること
