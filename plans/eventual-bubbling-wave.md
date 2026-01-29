# コードレビュー指摘事項の修正計画

## 概要

前回のGUIバグ修正（c364d0b）に対するCodexのコードレビューで指摘された問題を修正する。

---

## 指摘された問題

### High: CLI実行時のDB優先問題
**問題**: DBに1件でもドキュメントがあるとCLI実行でも常にDB優先になり、`doc_root`の変更やファイル更新が無視される。

**原因箇所**: `src/genglossary/runs/executor.py:164-171`

### Medium: MSWハンドラとテストの未更新
**問題**: Cancel APIの変更（POST → DELETE）に伴い、MSWハンドラとテストが旧URLのまま。

**原因箇所**:
- `frontend/src/mocks/handlers.ts:420` - `http.post(.../:runId/cancel)`
- `frontend/src/__tests__/terms-workflow.test.tsx:276` - 同上

### Medium: ロジック重複
**問題**: `_execute_full`のDBロード部分と`_load_documents_from_db`が重複しており、将来の変更が二重管理になる。

**原因箇所**: `src/genglossary/runs/executor.py:163-171` と `executor.py:116-146`

### Low: プロジェクト詳細のキャッシュ無効化不足
**問題**: ファイル操作後、`projectKeys.detail(projectId)`を invalidate しないと詳細画面の`document_count`が古いまま。

**原因箇所**: `frontend/src/api/hooks/useFiles.ts:53,65,77`

---

## 修正計画

### Step 1: CLI/GUIモード判定の改善

**ファイル**: `src/genglossary/runs/executor.py`

**方針**: `doc_root`がデフォルト値（"."）以外の場合は、明示的にファイルシステムを優先する。これにより：
- GUI: `doc_root="."` → DB優先（DBにドキュメントがあればそれを使用）
- CLI: `doc_root="/path/to/docs"` → FS優先（doc_rootからファイルを読み込み）

```python
def _execute_full(self, conn, doc_root="."):
    # ...
    self._log("info", "Loading documents...")

    # CLI mode: doc_root が明示的に指定されている場合はFS優先
    use_filesystem = doc_root != "."

    if use_filesystem:
        # CLI mode: ファイルシステムから読み込み、既存DBドキュメントを置き換え
        loader = DocumentLoader()
        documents = loader.load_directory(doc_root)
        if not documents:
            raise RuntimeError("No documents found in doc_root")

        # 既存ドキュメントをクリアして新しいものを保存
        delete_all_documents(conn)
        for document in documents:
            content_hash = compute_content_hash(document.content)
            file_name = document.file_path.rsplit("/", 1)[-1]
            create_document(conn, file_name, document.content, content_hash)
    else:
        # GUI mode: DBドキュメントを使用、なければエラー
        documents = self._load_documents_from_db(conn)

    self._log("info", f"Loaded {len(documents)} documents")
```

**注意**: `delete_all_documents`のimportを復活させる必要がある。

### Step 2: ロジック重複の解消

**ファイル**: `src/genglossary/runs/executor.py`

`_execute_full`のDB読み込み部分で`_load_documents_from_db`を再利用する。

### Step 3: MSWハンドラの修正

**ファイル**: `frontend/src/mocks/handlers.ts`

```typescript
// 修正前 (420行目)
http.post(`${BASE_URL}/api/projects/:projectId/runs/:runId/cancel`, () => {
  return HttpResponse.json({ ...mockCurrentRun, status: 'cancelled' })
}),

// 修正後
http.delete(`${BASE_URL}/api/projects/:projectId/runs/:runId`, () => {
  return HttpResponse.json({ message: 'Run cancelled' })
}),
```

### Step 4: テストの修正

**ファイル**: `frontend/src/__tests__/terms-workflow.test.tsx`

```typescript
// 修正前 (276行目)
http.post(`${BASE_URL}/api/projects/:projectId/runs/:runId/cancel`, () => {
  return HttpResponse.json({ ...mockRunRunning, status: 'cancelled' })
}),

// 修正後
http.delete(`${BASE_URL}/api/projects/:projectId/runs/:runId`, () => {
  return HttpResponse.json({ message: 'Run cancelled' })
}),
```

### Step 5: プロジェクト詳細のinvalidation追加

**ファイル**: `frontend/src/api/hooks/useFiles.ts`

3つのミューテーション（useCreateFile, useCreateFilesBulk, useDeleteFile）の`onSuccess`に追加:

```typescript
queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) })
```

### Step 6: テスト更新

**ファイル**: `tests/runs/test_executor.py`

新しいCLI/GUI判定ロジックに対応するテストを更新・追加:
- `doc_root="."` の場合はDB優先
- `doc_root="/custom/path"` の場合はFS優先でDBを上書き

---

## 修正対象ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `src/genglossary/runs/executor.py` | CLI/GUIモード判定改善、ロジック重複解消 |
| `tests/runs/test_executor.py` | テスト更新 |
| `frontend/src/mocks/handlers.ts` | cancel API のMSWハンドラ修正 |
| `frontend/src/__tests__/terms-workflow.test.tsx` | cancel API のテスト修正 |
| `frontend/src/api/hooks/useFiles.ts` | projectKeys.detail invalidation追加 |

---

## 検証方法

### バックエンドテスト
```bash
uv run pytest tests/runs/test_executor.py -v
```

### フロントエンドテスト
```bash
cd frontend && npm test
```

### 手動テスト
1. GUIでファイル登録 → Run実行 → 正常動作を確認
2. CLIで `doc_root` を指定してrun実行 → ファイルシステムから読み込まれることを確認
3. ファイル操作後にプロジェクト詳細画面でドキュメント数が更新されることを確認
