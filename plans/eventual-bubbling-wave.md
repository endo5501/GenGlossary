# GUI バグ修正計画

## 問題の概要

GUI機能で3つのバグが報告されている:
1. ファイル登録後、プロジェクト一覧のドキュメント数が0のまま
2. ファイル登録後にRunを実行しても何も起きない。STOPも反応しない
3. ブラウザリロードで登録ファイルが消える

## 根本原因の分析

### Bug 1: ドキュメント数が0のまま
**原因**: `useCreateFilesBulk` 等のフックが `fileKeys.list(projectId)` のみ invalidate し、`projectKeys.lists()` を invalidate していない。React Query の staleTime が5分のため、古いキャッシュ (document_count=0) がプロジェクト一覧に表示される。

### Bug 2: Run が動かない / STOP が効かない
3つの原因がある:
- **2a**: `_execute_full()` が `DocumentLoader().load_directory(doc_root)` でファイルシステムからドキュメントを読み込むが、GUI経由のファイルはDBに保存されており、`doc_root` は空。RuntimeError で即座に失敗する。
- **2b**: `_clear_tables_for_scope("full")` がドキュメントをDBから全削除してからファイルシステム読み込みに失敗するため、データが破壊される。
- **2c**: キャンセルAPIのHTTPメソッドとURL不一致。フロントエンドは `POST .../cancel` を送信するが、バックエンドは `DELETE .../{run_id}` を期待。

### Bug 3: リロードでファイル消失
Bug 2b の結果。Run実行時に `delete_all_documents()` でDBのドキュメントが全削除され、ファイルシステムからの読み込みも失敗するため、以降DBは空になる。

---

## 修正計画

### Step 1: `_clear_tables_for_scope("full")` のドキュメント削除を除去

**ファイル**: `src/genglossary/runs/executor.py` (338-351行目)

`scope == "full"` の場合から `delete_all_documents(conn)` の呼び出しを削除する。ドキュメントはパイプラインの入力データであり、再実行時に削除すべきでない。

```python
if scope == "full":
    # delete_all_documents(conn)  ← 削除
    delete_all_terms(conn)
    delete_all_provisional(conn)
    delete_all_issues(conn)
    delete_all_refined(conn)
```

また、未使用になる `delete_all_documents` の import を削除:
```python
from genglossary.db.document_repository import (
    create_document,
    # delete_all_documents,  ← 削除
    list_all_documents,
)
```

### Step 2: `_execute_full()` をDB優先のドキュメント読み込みに変更

**ファイル**: `src/genglossary/runs/executor.py` (149-200行目)

`_execute_full()` の Step 1 (ドキュメント読み込み) を以下のように変更:
1. まず `list_all_documents(conn)` でDBを確認
2. DBにドキュメントがあればそのまま使用 (GUIモード)
3. なければ `DocumentLoader().load_directory(doc_root)` で読み込み、DBに保存 (CLIモード)

```python
def _execute_full(self, conn, doc_root="."):
    if self._check_cancellation():
        return

    self._log("info", "Loading documents...")
    doc_rows = list_all_documents(conn)

    if doc_rows:
        # GUIモード: DBのドキュメントを使用
        documents = [
            Document(file_path=row["file_name"], content=row["content"])
            for row in doc_rows
        ]
    else:
        # CLIモード: ファイルシステムから読み込み
        loader = DocumentLoader()
        documents = loader.load_directory(doc_root)
        if not documents:
            raise RuntimeError("No documents found in doc_root")
        for document in documents:
            content_hash = compute_content_hash(document.content)
            file_name = document.file_path.rsplit("/", 1)[-1]
            create_document(conn, file_name, document.content, content_hash)

    self._log("info", f"Loaded {len(documents)} documents")
    # Step 2以降は従来通り...
```

### Step 3: テスト更新

**ファイル**: `tests/runs/test_executor.py`

1. **`test_re_execution_clears_tables` (408-450行目)**: `delete_all_documents` のモックと assert を削除。他のテーブル (terms, provisional, issues, refined) のクリアは引き続き検証。

2. **新規テスト追加**: DBにドキュメントがある場合、`DocumentLoader.load_directory` が呼ばれず、DBドキュメントが使用されることを検証。

3. **既存テストの確認**: `test_full_scope_executes_all_steps` 等はDBが空のため従来通りファイルシステムパスを通り、変更不要。

### Step 4: キャンセルAPIの修正

**ファイル**: `frontend/src/api/hooks/useRuns.ts` (15-16行目)

```typescript
// 修正前
cancel: (projectId: number, runId: number) =>
    apiClient.post<RunResponse>(`/api/projects/${projectId}/runs/${runId}/cancel`, {}),

// 修正後
cancel: (projectId: number, runId: number) =>
    apiClient.delete<{ message: string }>(`/api/projects/${projectId}/runs/${runId}`),
```

変更点: `post` → `delete`、URL末尾の `/cancel` を削除、戻り値型をバックエンド仕様に合わせる。

### Step 5: ファイル操作後のプロジェクトリスト invalidation 追加

**ファイル**: `frontend/src/api/hooks/useFiles.ts`

`projectKeys` を `useProjects.ts` から import し、`useCreateFile`、`useCreateFilesBulk`、`useDeleteFile` の3つの `onSuccess` に `projectKeys.lists()` の invalidation を追加:

```typescript
import { projectKeys } from './useProjects'

// 各ミューテーションの onSuccess に追加:
queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
```

---

## 修正対象ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/runs/executor.py` | `_execute_full()` DB優先読み込み、`_clear_tables_for_scope()` ドキュメント削除除去 |
| `tests/runs/test_executor.py` | テスト更新・追加 |
| `frontend/src/api/hooks/useRuns.ts` | cancel API のメソッド・URL修正 |
| `frontend/src/api/hooks/useFiles.ts` | projectKeys invalidation 追加 |

---

## 検証方法

### 自動テスト
```bash
uv run pytest tests/runs/test_executor.py -v
```

### 手動テスト (GUI)
1. プロジェクト作成 → Files でテキストファイル登録 → プロジェクト一覧に戻り、ドキュメント数が正しく表示されることを確認
2. Files でファイル登録 → Run ボタンクリック → パイプラインが実行されることを確認 (LLMが起動している必要あり、またはログパネルでエラーメッセージを確認)
3. Run 実行中に Stop ボタンをクリック → 実行がキャンセルされることを確認
4. ファイル登録後にブラウザリロード → ファイルが維持されていることを確認
5. ファイル登録 → Run → リロード → ファイルが維持されていることを確認
