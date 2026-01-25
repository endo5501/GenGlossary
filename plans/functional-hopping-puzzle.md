# 実装計画: Provisional Regenerate Endpoint

## 概要

`POST /api/projects/{project_id}/provisional/{entry_id}/regenerate` エンドポイントを実装する。
現在はTODOプレースホルダーで既存値をそのまま返しているが、LLMを使用して定義を再生成するように変更する。

## TDDワークフロー

### Phase 1: Red (テスト追加)

#### 変更ファイル
- `tests/api/routers/test_provisional.py`

#### 追加するテストケース

1. **test_regenerate_provisional_changes_definition_with_mock**
   - LLMをモックして新しい定義を返す
   - 旧定義 ("旧定義") とは異なる値が返されることを検証

2. **test_regenerate_provisional_updates_confidence_with_mock**
   - LLMをモックして新しいconfidenceを返す
   - confidence が更新されることを検証

3. **test_regenerate_provisional_persists_to_db**
   - regenerate後にGETで取得して永続化を検証

4. **test_regenerate_provisional_llm_timeout_returns_503**
   - LLMがタイムアウトした場合に503を返す

5. **test_regenerate_provisional_llm_unavailable_returns_503**
   - LLM接続エラー時に503を返す

#### モック戦略

```python
from unittest.mock import MagicMock, patch

# GlossaryGenerator._generate_definition をモック
@patch("genglossary.api.routers.provisional.GlossaryGenerator")
def test_regenerate_...(mock_generator_class, ...):
    mock_generator = MagicMock()
    mock_generator._generate_definition.return_value = ("新しい定義", 0.85)
    mock_generator_class.return_value = mock_generator
```

#### fixture修正
- `test_project_setup`に`llm_provider="ollama"`を設定
- テスト用ドキュメントを`doc_root`に作成

### Phase 2: Green (実装)

#### 変更ファイル
- `src/genglossary/api/routers/provisional.py`

#### 必要なインポート追加

```python
import httpx
from genglossary.api.dependencies import get_project_by_id
from genglossary.document_loader import DocumentLoader
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.llm.factory import create_llm_client
from genglossary.models.project import Project
```

#### エンドポイント実装

```python
@router.post("/{entry_id}/regenerate", response_model=ProvisionalResponse)
async def regenerate_provisional(
    project_id: int = Path(..., description="Project ID"),
    entry_id: int = Path(..., description="Entry ID"),
    project: Project = Depends(get_project_by_id),  # 追加
    project_db: sqlite3.Connection = Depends(get_project_db),
) -> ProvisionalResponse:
    # 1. 用語の存在確認
    row = get_provisional_term(project_db, entry_id)
    if row is None:
        raise HTTPException(status_code=404, ...)

    try:
        # 2. LLMクライアント作成
        llm_client = create_llm_client(project.llm_provider, project.llm_model or None)

        # 3. ドキュメントロード
        loader = DocumentLoader()
        documents = loader.load_directory(project.doc_root)

        # 4. GlossaryGeneratorで再生成
        generator = GlossaryGenerator(llm_client=llm_client)
        occurrences = generator._find_term_occurrences(row["term_name"], documents)
        if not occurrences:
            occurrences = row["occurrences"]
        definition, confidence = generator._generate_definition(row["term_name"], occurrences)

        # 5. DB更新
        update_provisional_term(project_db, entry_id, definition, confidence)

        # 6. 更新後の値を返す
        updated_row = get_provisional_term(project_db, entry_id)
        return ProvisionalResponse.from_db_row(updated_row)

    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="LLM service timeout")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {e}")
```

### Phase 3: Refactor & Documentation

#### ドキュメント更新
- `docs/architecture.md` - APIエンドポイントの説明更新

## エラーハンドリング

| エラー | HTTPステータス | メッセージ |
|--------|---------------|-----------|
| 用語が見つからない | 404 | Entry {entry_id} not found |
| LLMタイムアウト | 503 | LLM service timeout |
| LLM接続エラー | 503 | LLM service unavailable: {details} |

## 重要ファイル

### 実装対象
- `src/genglossary/api/routers/provisional.py:101-128` - TODOを実装

### テスト対象
- `tests/api/routers/test_provisional.py:163-182` - テスト強化

### 参照
- `src/genglossary/glossary_generator.py:216-254` - `_generate_definition()` メソッド
- `src/genglossary/cli_db.py:733-783` - CLI参照実装
- `src/genglossary/llm/factory.py` - LLMクライアント生成

## 検証方法

### 単体テスト
```bash
uv run pytest tests/api/routers/test_provisional.py -v
```

### 静的解析
```bash
uv run pyright
```

### 全テスト
```bash
uv run pytest
```

### 手動確認（オプション）
```bash
# APIサーバー起動
uv run uvicorn genglossary.api.main:app --reload

# エンドポイント呼び出し（LLMが起動している場合）
curl -X POST http://localhost:8000/api/projects/1/provisional/1/regenerate
```
