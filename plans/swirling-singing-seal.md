# コードレビュー指摘修正計画

## 概要

codex MCPによるコードレビューで指摘された問題を修正する。
認証関連は別チケット（`260127-123553-api-authentication.md`）で対応。

---

## 修正対象（5件）

| # | 重要度 | 問題 | ファイル |
|---|--------|------|----------|
| 1 | Medium | CloneDialog state が prop 変更に反応しない | `CloneProjectDialog.tsx` |
| 2 | Medium | Clone request の new_name バリデーション不足 | `project_schemas.py` |
| 3 | Medium | Create/Clone 失敗時に orphan DB ファイル | `projects.py` |
| 4 | Low | SPA で window.location.href 使用 | `HomePage.tsx`, `FilesPage.tsx` |
| 5 | Low | Delete loading state がグローバル | `FilesPage.tsx` |

---

## Step 1: CloneDialog state 修正

**ファイル**: `frontend/src/components/dialogs/CloneProjectDialog.tsx`

**問題**: ダイアログを閉じずに別プロジェクトを選択すると、古い名前が残る

**修正**:
```typescript
import { useEffect } from 'react'

// 既存の useState の後に追加
useEffect(() => {
  if (opened) {
    setNewName(`${project.name} (Copy)`)
    setError(null)
  }
}, [opened, project.id])
```

---

## Step 2: ProjectCloneRequest バリデーション追加

**ファイル**: `src/genglossary/api/schemas/project_schemas.py`

**修正**: `ProjectCloneRequest` に `validate_name` を追加

```python
class ProjectCloneRequest(BaseModel):
    """Request schema for cloning a project."""

    new_name: str = Field(..., description="Name for the cloned project")

    @field_validator("new_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name is not empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be empty")
        return stripped
```

---

## Step 3: Create/Clone のエラー時クリーンアップ

**ファイル**: `src/genglossary/api/routers/projects.py`

**修正**: `create_new_project` と `clone_existing_project` で例外時に DB ファイル削除

```python
from pathlib import Path

# create_new_project 内
except sqlite3.IntegrityError:
    # Cleanup orphaned DB file
    try:
        Path(db_path).unlink(missing_ok=True)
    except Exception:
        pass
    raise HTTPException(...)

# clone_existing_project 内
except sqlite3.IntegrityError:
    # Cleanup orphaned cloned DB file
    try:
        Path(new_db_path).unlink(missing_ok=True)
    except Exception:
        pass
    raise HTTPException(...)
```

---

## Step 4: ルーターナビゲーションに変更

**ファイル**: `frontend/src/pages/HomePage.tsx`, `frontend/src/pages/FilesPage.tsx`

**修正**: `window.location.href` → `useNavigate()` に変更

```typescript
// HomePage.tsx
import { useNavigate } from '@tanstack/react-router'

export function HomePage() {
  const navigate = useNavigate()

  // onOpen 内
  navigate({ to: `/projects/${selectedProject.id}/files` })
}

// FilesPage.tsx 同様
navigate({ to: `/projects/${projectId}/document-viewer`, search: { file: file.id } })
```

---

## Step 5: 個別ファイルの削除 loading 状態

**ファイル**: `frontend/src/pages/FilesPage.tsx`

**修正**: `deletingFileIds` state で個別管理

```typescript
const [deletingFileId, setDeletingFileId] = useState<number | null>(null)

const handleDeleteFile = async (fileId: number) => {
  setDeletingFileId(fileId)
  try {
    await deleteFileMutation.mutateAsync(fileId)
  } catch (err) {
    console.error('Delete failed:', err)
  } finally {
    setDeletingFileId(null)
  }
}

// ボタン
<Button loading={deletingFileId === file.id}>
```

---

## 修正対象ファイル一覧

| ファイル | 修正内容 |
|----------|----------|
| `frontend/src/components/dialogs/CloneProjectDialog.tsx` | useEffect 追加 |
| `src/genglossary/api/schemas/project_schemas.py` | バリデーター追加 |
| `src/genglossary/api/routers/projects.py` | クリーンアップ追加 |
| `frontend/src/pages/HomePage.tsx` | useNavigate 使用 |
| `frontend/src/pages/FilesPage.tsx` | useNavigate + deletingFileId |

---

## 検証方法

1. **バックエンドテスト**: `uv run pytest tests/api/routers/test_projects.py -v`
2. **フロントエンドテスト**: `cd frontend && npm run test`
3. **ビルド確認**: `cd frontend && npm run build`
4. **静的解析**: `uv run pyright`
5. **手動確認**:
   - プロジェクト選択後にCloneダイアログを開き、別プロジェクト選択 → 名前が更新されること
   - 重複名でプロジェクト作成/クローン → orphan ファイルが残らないこと
   - ページ遷移でフルリロードしないこと
   - ファイル削除中に他の削除ボタンが影響されないこと
