# Files画面 Addボタン改善 - 実装計画

## 概要

Files画面のAddボタンを、テキスト入力方式からHTML5 File APIを使用したファイル選択ダイアログに改善する。

### 変更方針
- **HTML5 File API**を使用（Electronは導入しない）
- ファイルの**内容（content）**をDBに保存
- 用語抽出処理・ドキュメントビューアでコンテンツを直接使用可能に

## 変更対象ファイル

### バックエンド
| ファイル | 変更内容 |
|----------|----------|
| `src/genglossary/db/schema.py` | documentsテーブルにcontentカラム追加 |
| `src/genglossary/db/document_repository.py` | CRUD関数をcontent対応に変更 |
| `src/genglossary/api/schemas/file_schemas.py` | リクエスト/レスポンススキーマ変更 |
| `src/genglossary/api/routers/files.py` | APIエンドポイント変更（content受け取り） |
| `src/genglossary/runs/executor.py` | DBからcontentを取得するように変更 |

### フロントエンド
| ファイル | 変更内容 |
|----------|----------|
| `frontend/package.json` | @mantine/dropzone追加 |
| `frontend/src/api/types.ts` | 型定義変更（file_path→file_name, content追加） |
| `frontend/src/api/hooks/useFiles.ts` | 複数ファイル一括作成hook追加 |
| `frontend/src/components/dialogs/AddFileDialog.tsx` | Dropzone UIに書き換え |

### テスト
| ファイル | 変更内容 |
|----------|----------|
| `tests/db/test_schema.py` | contentカラムのテスト追加 |
| `tests/db/test_document_repository.py` | content対応のテスト追加 |
| `tests/api/routers/test_files.py` | 新APIのテスト追加 |
| `frontend/src/__tests__/components/dialogs/AddFileDialog.test.tsx` | UIテスト更新 |

---

## 実装ステップ（TDDアプローチ）

### Phase 0: チケット更新

元のチケット（`current-ticket.md`）を本計画の内容に合わせて更新する。

#### 主な変更点
- **Electron → HTML5 File API**: Electronは導入せず、ブラウザ標準のFile APIを使用
- **ファイルパス → ファイル内容**: ファイルパスではなく、ファイルの内容をDBに保存
- **バックエンド変更追加**: DBスキーマ、API、PipelineExecutorの変更が必要
- **diff-scan機能**: GUIからは使用不可になる旨を記載

#### 更新後のチケット内容
```markdown
## 改善内容

- Addボタンを押すとファイル選択ダイアログを表示（HTML5 File API + Mantine Dropzone）
- テキストファイル（.txt, .md）のみをフィルタリング
- 複数ファイルを同時に選択可能
- 選択したファイルの内容をDBに保存し、プロジェクトに登録
- ファイルシステムへの依存を排除（ファイル内容をDBに直接保存）

## Notes

- HTML5 File APIとMantine Dropzoneを使用してファイル選択UIを実装
- FileReader APIでファイル内容を読み取り、バックエンドに送信
- DBスキーマを変更し、documentsテーブルにcontentカラムを追加
- PipelineExecutorはDBから直接ファイル内容を取得（ファイルシステム再読み込み不要）
- diff-scan機能はGUIからは使用不可（ファイルシステムにアクセスできないため）
```

---

### Phase 1: バックエンド - DBスキーマ変更

#### Step 1.1: テスト作成 - documentsテーブルにcontentカラム
```python
# tests/db/test_schema.py
def test_documents_table_has_content_column(in_memory_db):
    initialize_db(in_memory_db)
    cursor = in_memory_db.cursor()
    cursor.execute("PRAGMA table_info(documents)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    assert "content" in columns
    assert "file_name" in columns  # file_path → file_name
```

#### Step 1.2: 実装 - schema.py
```sql
-- documents テーブル変更
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL UNIQUE,  -- file_path → file_name
    content TEXT NOT NULL,           -- 新規追加
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```
- `SCHEMA_VERSION`: 3 → 4
- マイグレーション関数追加（既存テーブルにカラム追加）

---

### Phase 2: バックエンド - document_repository変更

#### Step 2.1: テスト作成
```python
# tests/db/test_document_repository.py
def test_create_document_with_content(db_with_schema):
    doc_id = create_document(
        db_with_schema,
        file_name="test.md",
        content="# Test Content",
        content_hash="abc123"
    )
    doc = get_document(db_with_schema, doc_id)
    assert doc["content"] == "# Test Content"
    assert doc["file_name"] == "test.md"
```

#### Step 2.2: 実装 - document_repository.py
```python
def create_document(
    conn: sqlite3.Connection,
    file_name: str,
    content: str,
    content_hash: str
) -> int:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (file_name, content, content_hash) VALUES (?, ?, ?)",
        (file_name, content, content_hash),
    )
    conn.commit()
    return cast(int, cursor.lastrowid)
```

---

### Phase 3: バックエンド - APIスキーマ変更

#### Step 3.1: スキーマ定義
```python
# src/genglossary/api/schemas/file_schemas.py
class FileCreateRequest(BaseModel):
    file_name: str = Field(..., description="ファイル名")
    content: str = Field(..., description="ファイル内容")

class FileCreateBulkRequest(BaseModel):
    files: list[FileCreateRequest]

class FileResponse(BaseModel):
    id: int
    file_name: str
    content_hash: str
```

---

### Phase 4: バックエンド - APIエンドポイント変更

#### Step 4.1: テスト作成
```python
# tests/api/routers/test_files.py
def test_create_file_with_content(test_project_setup, client):
    payload = {"file_name": "test.md", "content": "# Hello"}
    response = client.post(f"/api/projects/{project_id}/files", json=payload)
    assert response.status_code == 201
    assert response.json()["file_name"] == "test.md"

def test_create_files_bulk(test_project_setup, client):
    payload = {"files": [
        {"file_name": "a.md", "content": "A"},
        {"file_name": "b.txt", "content": "B"}
    ]}
    response = client.post(f"/api/projects/{project_id}/files/bulk", json=payload)
    assert response.status_code == 201
    assert len(response.json()) == 2
```

#### Step 4.2: 実装 - files.py
- `POST /api/projects/{id}/files` - 単一ファイル追加（content受け取り）
- `POST /api/projects/{id}/files/bulk` - 複数ファイル一括追加（新規）
- 拡張子バリデーション: `.txt`, `.md`のみ許可
- ファイル名バリデーション: `/`を含まない

---

### Phase 5: バックエンド - PipelineExecutor変更

#### Step 5.1: テスト作成
```python
# tests/runs/test_executor.py
def test_load_documents_from_db_uses_content(db_with_documents):
    executor = PipelineExecutor()
    documents = executor._load_documents_from_db(conn)
    assert documents[0].content == "expected content from DB"
```

#### Step 5.2: 実装 - executor.py `_load_documents_from_db`
```python
def _load_documents_from_db(self, conn: sqlite3.Connection) -> list[Document]:
    doc_rows = list_all_documents(conn)
    documents = []
    for row in doc_rows:
        doc = Document(
            file_path=row["file_name"],  # file_nameをfile_pathとして使用
            content=row["content"]       # DBから直接取得
        )
        documents.append(doc)
    return documents
```

**重要**: ファイルシステムからの再読み込み（DocumentLoader）を削除

---

### Phase 6: フロントエンド - パッケージ追加

```bash
cd frontend && pnpm add @mantine/dropzone
```

---

### Phase 7: フロントエンド - 型定義・hooks更新

#### types.ts
```typescript
export interface FileResponse {
  id: number
  file_name: string  // file_path → file_name
  content_hash: string
}

export interface FileCreateRequest {
  file_name: string
  content: string
}
```

#### useFiles.ts
```typescript
export function useCreateFiles(projectId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (files: FileCreateRequest[]) =>
      apiClient.post(`/api/projects/${projectId}/files/bulk`, { files }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) })
    },
  })
}
```

---

### Phase 8: フロントエンド - AddFileDialog書き換え

#### 主な変更点
1. `TextInput` → `Dropzone`（@mantine/dropzone）
2. 複数ファイル選択対応
3. `FileReader API`でファイル内容を読み取り
4. `.txt`, `.md`のみフィルタリング

#### 新しいUI構成
```
┌─────────────────────────────────────┐
│  Add Files                      [×] │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  │   Drag files here or click  │    │
│  │   to select                 │    │
│  │                             │    │
│  │   Only .txt and .md files   │    │
│  └─────────────────────────────┘    │
│                                     │
│  Selected Files (2)                 │
│  ├─ document1.md         [Remove]   │
│  └─ notes.txt            [Remove]   │
│                                     │
│            [Cancel]  [Add (2)]      │
└─────────────────────────────────────┘
```

---

## 影響を受ける既存機能

### diff-scan機能
- **現状**: ファイルシステムをスキャンして変更検出
- **影響**: ブラウザからのアップロードではファイルシステムにアクセス不可
- **対応**: GUIからは使用不可にする（将来的に別アプローチで再実装検討）

### FilesPage表示
- `file_path` → `file_name` に変更
- 表示内容に大きな影響なし

---

## 検証方法

### バックエンドテスト
```bash
uv run pytest tests/db/test_schema.py -v
uv run pytest tests/db/test_document_repository.py -v
uv run pytest tests/api/routers/test_files.py -v
uv run pytest tests/runs/test_executor.py -v
```

### フロントエンドテスト
```bash
cd frontend && pnpm test
```

### 静的解析
```bash
uv run pyright
cd frontend && pnpm run lint
```

### E2E手動テスト
1. プロジェクト作成
2. Addボタンクリック → Dropzoneダイアログ表示
3. .md/.txtファイルをドラッグ&ドロップ
4. 複数ファイル選択
5. Addボタンクリック → ファイル一覧に追加される
6. パイプライン実行 → 用語抽出が正常に動作
