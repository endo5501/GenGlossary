# コードレビュー指摘対応計画

## 概要
チケット `260124-164009-gui-api-data-endpoints` のコードレビュー指摘事項に対応する。

## 対応方針決定済み
- **regenerate TODO**: 別チケットに切り出し（このチケットでは対応しない）
- **DELETE 挙動**: 404 を返すように修正
- **PATCH 部分更新**: 現状維持（全フィールド必須）

---

## 修正内容

### 1. [重大] パストラバーサル脆弱性の修正
**ファイル**: `src/genglossary/api/routers/files.py`

**現状**:
```python
file_full_path = FilePath(project.doc_root) / request.file_path
```

**修正**:
- `resolve()` でパスを正規化
- `doc_root` 配下かを検証
- `is_file()` でファイル存在確認
- 違反時は 400 エラー

```python
# Resolve and validate file path
doc_root = FilePath(project.doc_root).resolve()
file_full_path = (doc_root / request.file_path).resolve()

# Security check: ensure path is within doc_root
if not str(file_full_path).startswith(str(doc_root) + "/"):
    raise HTTPException(status_code=400, detail="Invalid file path")

# Check if file exists and is a file
if not file_full_path.is_file():
    raise HTTPException(status_code=400, detail=f"File not found: {request.file_path}")
```

### 2. [高] UNIQUE 制約違反のエラーハンドリング
**ファイル**:
- `src/genglossary/api/routers/files.py` (create_file)
- `src/genglossary/api/routers/terms.py` (create_new_term)

**修正**:
- `sqlite3.IntegrityError` をキャッチして 409 Conflict を返す

```python
try:
    doc_id = create_document(project_db, request.file_path, content_hash)
except sqlite3.IntegrityError:
    raise HTTPException(status_code=409, detail=f"File already exists: {request.file_path}")
```

### 3. DELETE で 404 を返す
**ファイル**:
- `src/genglossary/api/routers/files.py` (delete_file)
- `src/genglossary/api/routers/terms.py` (delete_existing_term)

**修正**:
- 削除前に存在確認を行い、存在しない場合は 404 を返す

```python
# Check if file exists
row = get_document(project_db, file_id)
if row is None:
    raise HTTPException(status_code=404, detail=f"File {file_id} not found")

delete_document(project_db, file_id)
```

### 4. [低] テストでレジストリパス固定
**ファイル**: `tests/api/conftest.py` (または適切な conftest)

**修正**:
- autouse fixture で `GENGLOSSARY_REGISTRY_PATH` を一時パスに設定

```python
@pytest.fixture(autouse=True)
def isolate_registry(tmp_path, monkeypatch):
    """Ensure tests don't touch user's registry."""
    test_registry = tmp_path / "test_registry.db"
    monkeypatch.setenv("GENGLOSSARY_REGISTRY_PATH", str(test_registry))
```

---

## 対応しない項目
- **regenerate TODO**: 別チケットで LLM 統合と共に対応
- **regenerate テスト不十分**: 上記に伴い別チケットで対応
- **PATCH 部分更新**: 現状維持の方針

---

## テスト計画
1. パストラバーサル攻撃のテスト追加 (`../` や絶対パスの拒否)
2. UNIQUE 制約違反テスト追加（409 レスポンス確認）
3. DELETE 404 テスト追加（存在しないリソース削除時）
4. 既存テスト全て通過確認

---

## 検証手順
```bash
# 静的解析
uv run pyright

# 全テスト実行
uv run pytest

# 手動確認（任意）
# - POST /files で ../secret.txt のようなパスを送信 → 400
# - POST /files で既存ファイルを再登録 → 409
# - DELETE /files/{存在しないID} → 404
```

---

## 修正対象ファイル一覧
1. `src/genglossary/api/routers/files.py` - パストラバーサル、UNIQUE、DELETE 404
2. `src/genglossary/api/routers/terms.py` - UNIQUE、DELETE 404
3. `tests/api/conftest.py` - レジストリパス固定
4. `tests/api/routers/test_files.py` - テスト追加
5. `tests/api/routers/test_terms.py` - テスト追加
