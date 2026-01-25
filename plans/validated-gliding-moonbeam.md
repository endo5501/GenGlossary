# 用語カテゴリ保存機能の実装計画

## 概要

TermExtractor が用語抽出時に取得したカテゴリ情報を DB に保存し、`common_noun` のスキップを用語集生成時に遅延させる。

## 変更の目的

- 全分類結果（`common_noun` 含む）を `terms_extracted` テーブルに保存
- `common_noun` 除外を抽出時でなく用語集生成時に行う
- 後方互換性を維持しつつ、カテゴリ情報を返すオプションを追加

---

## 実装計画

### Phase 1: ClassifiedTerm モデル追加

**ファイル**: `src/genglossary/models/term.py`

```python
class ClassifiedTerm(BaseModel):
    """分類済みの用語"""
    term: str
    category: TermCategory
```

**テスト** (`tests/models/test_term.py`):
- ClassifiedTerm の作成と検証

---

### Phase 2: TermExtractor の拡張

**ファイル**: `src/genglossary/term_extractor.py`

**変更**:
1. `return_categories: bool = False` パラメータを追加
2. `@overload` で型安全なシグネチャを定義
3. `return_categories=True` の場合、全カテゴリ（`common_noun` 含む）を `list[ClassifiedTerm]` で返す
4. `return_categories=False` の場合、既存動作（`list[str]`、`common_noun` 除外）

**テスト** (`tests/test_term_extractor.py`):
- `return_categories=False` で既存動作を維持
- `return_categories=True` で `list[ClassifiedTerm]` を返す
- `return_categories=True` で `common_noun` を含む

---

### Phase 3: GlossaryGenerator の拡張

**ファイル**: `src/genglossary/glossary_generator.py`

**変更**:
1. `terms` パラメータの型を `list[str] | list[ClassifiedTerm]` に拡張
2. `skip_common_nouns: bool = True` パラメータを追加
3. `ClassifiedTerm` リスト受信時、`skip_common_nouns=True` なら `common_noun` をスキップ

**テスト** (`tests/test_glossary_generator.py`):
- `list[str]` 入力で既存動作維持
- `list[ClassifiedTerm]` 入力で `common_noun` をスキップ
- `skip_common_nouns=False` で全カテゴリ処理

---

### Phase 4: CLI の更新

**ファイル**: `src/genglossary/cli.py` (`_generate_glossary_with_db`)

**変更**:
1. `extract_terms(..., return_categories=True)` を呼び出し
2. 全用語（`common_noun` 含む）を DB に保存:
   ```python
   for ct in classified_terms:
       create_term(conn, ct.term, category=ct.category.value)
   ```
3. `generator.generate(classified_terms, documents)` でカテゴリ情報を渡す

**ファイル**: `src/genglossary/cli_db.py`

**変更**:
- `terms_regenerate()`: カテゴリ付きで保存
- `provisional_regenerate()`: DB から読み込んで `ClassifiedTerm` を再構築

---

### Phase 5: 検証と仕上げ

1. `uv run pyright` で静的解析パス
2. `uv run pytest` で全テストパス
3. `docs/architecture.md` 更新

---

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/genglossary/models/term.py` | `ClassifiedTerm` モデル追加 |
| `src/genglossary/term_extractor.py` | `return_categories` パラメータ追加、オーバーロード |
| `src/genglossary/glossary_generator.py` | `ClassifiedTerm` 対応、`skip_common_nouns` 追加 |
| `src/genglossary/cli.py` | カテゴリ付き抽出・保存 |
| `src/genglossary/cli_db.py` | カテゴリ付き抽出・保存・再構築 |
| `tests/models/test_term.py` | `ClassifiedTerm` テスト |
| `tests/test_term_extractor.py` | `return_categories` テスト |
| `tests/test_glossary_generator.py` | `ClassifiedTerm` 入力テスト |
| `docs/architecture.md` | ドキュメント更新 |

---

## データフロー（変更後）

```
TermExtractor.extract_terms(return_categories=True)
    ↓
list[ClassifiedTerm]（全カテゴリ含む）
    ↓
CLI: create_term(conn, term, category)  ← カテゴリ付きでDB保存
    ↓
GlossaryGenerator.generate(classified_terms, skip_common_nouns=True)
    ↓
common_noun をスキップして定義生成
```

---

## 検証方法

1. **単体テスト**: `uv run pytest tests/models/test_term.py tests/test_term_extractor.py tests/test_glossary_generator.py -v`
2. **静的解析**: `uv run pyright`
3. **全テスト**: `uv run pytest`
4. **E2E確認**: 実際にドキュメントを処理し、DB の `terms_extracted` テーブルに `category` が保存されていることを確認

---

## 注意事項

- **後方互換性**: `return_categories=False`（デフォルト）で既存動作を維持
- **既存DBデータ**: `category=NULL` の既存データは `common_noun` として扱う（用語集生成時にスキップ）
- **LLM呼び出し**: 重複呼び出しを避け、分類結果を再利用

---

## 決定事項

- 既存DBの `category=NULL` データ → `common_noun` として扱い、用語集生成時にスキップ

---

# バグ修正計画: 重複用語によるIntegrityError

## 概要

`return_categories=True` パスで用語の重複排除が行われていないため、LLMが同じ用語を複数カテゴリに分類した場合、DB挿入時に `sqlite3.IntegrityError` が発生する。

## 問題の詳細

### 現状

| パス | 重複排除 | 状態 |
|------|----------|------|
| `return_categories=False` | `_process_terms()` で実施 | ✅ 安全 |
| `return_categories=True` | なし | ❌ **IntegrityError リスク** |

### 発生シナリオ

1. LLMが同じ用語を `person_name` と `technical_term` の両方に分類
2. `_get_classified_terms()` で2つの `ClassifiedTerm` オブジェクトが生成
3. CLI で DB 挿入時に `terms_extracted.term_text` の UNIQUE 制約違反

---

## 修正計画

### Phase 1: テスト作成（Red）

**ファイル**: `tests/test_term_extractor.py`

**追加するテスト**:

```python
def test_get_classified_terms_deduplicates_same_term_in_multiple_categories(
    self, mock_llm_client: MagicMock, sample_document: Document
) -> None:
    """重複用語がある場合、最初に出現したカテゴリを採用（first wins）"""
    mock_llm_client.generate_structured.return_value = BatchTermClassificationResponse(
        classifications=[
            {"term": "量子コンピュータ", "category": "technical_term"},
            {"term": "量子コンピュータ", "category": "person_name"},  # 重複
            {"term": "量子ビット", "category": "technical_term"},
        ]
    )
    # ... setup ...
    result = extractor.extract_terms([sample_document], return_categories=True)

    # 重複が排除され、最初のカテゴリ（technical_term）が採用される
    terms_dict = {t.term: t for t in result}
    assert len(result) == 2
    assert terms_dict["量子コンピュータ"].category == TermCategory.TECHNICAL_TERM
```

### Phase 2: 実装（Green）

**ファイル**: `src/genglossary/term_extractor.py`

**変更**: `_get_classified_terms()` メソッドに重複排除ロジックを追加

```python
def _get_classified_terms(
    self, classification: TermClassificationResponse
) -> list[ClassifiedTerm]:
    """Convert classification results to list of ClassifiedTerm objects.

    Deduplicates terms using "first wins" strategy.
    """
    seen: set[str] = set()
    result: list[ClassifiedTerm] = []
    for category_str, terms in classification.classified_terms.items():
        for term in terms:
            stripped = term.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                result.append(
                    ClassifiedTerm(term=stripped, category=TermCategory(category_str))
                )
    return result
```

---

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/genglossary/term_extractor.py` | `_get_classified_terms()` に重複排除追加 |
| `tests/test_term_extractor.py` | 重複排除のテスト追加 |

---

## 検証方法

1. **単体テスト**: `uv run pytest tests/test_term_extractor.py -v -k deduplicate`
2. **全テスト**: `uv run pytest`
3. **静的解析**: `uv run pyright`

---

## 採用した解決策

- **First wins 戦略**: 同じ用語が複数カテゴリに分類された場合、最初に出現したカテゴリを採用
- 理由: シンプルで予測可能、`_process_terms()` の動作と一貫性がある

---

## 対応しない項目（Low Priority）

- **プログレス表示の不正確さ**: `common_noun` フィルタにより100%に達しない場合があるが、機能に影響しないため今回は対応しない

---

# 実装完了記録

## 実装日時

2026-01-25

## 実装内容

### 完了したフェーズ

1. ✅ **Phase 1: ClassifiedTermモデル追加** - 既に実装済み
2. ✅ **Phase 2: TermExtractorの拡張とバグ修正**
   - `return_categories`パラメータ: 既に実装済み
   - 重複用語の排除ロジック: `_process_batch_response`に実装 (first wins戦略)
   - テスト追加: `test_get_classified_terms_deduplicates_same_term_in_multiple_categories`
3. ✅ **Phase 3: GlossaryGeneratorの拡張** - 既に実装済み
   - `ClassifiedTerm`対応、`skip_common_nouns`パラメータ実装済み
4. ✅ **Phase 4: CLIの更新** - 既に実装済み
   - `cli.py`: `_generate_glossary_with_db`でカテゴリ付き抽出・保存
   - `cli_db.py`: `terms_regenerate`と`provisional_regenerate`でカテゴリ対応
5. ✅ **Phase 5: 検証と仕上げ**
   - 全テスト (461 passed): ✅
   - Pyright静的解析: ✅ (0 errors, 0 warnings)

### 実装の詳細

#### バグ修正: 重複用語のIntegrityError

**問題**: LLMが同じ用語を複数カテゴリに分類した場合、DB挿入時にUNIQUE制約違反

**解決策**: `_process_batch_response`で"first wins"戦略による重複排除を実装

```python
def _process_batch_response(
    self,
    response: BatchTermClassificationResponse,
    classified: dict[str, list[str]],
    seen_terms: set[str],  # ← 追加
) -> None:
    for item in response.classifications:
        term = item.get("term", "")
        category = item.get("category", "")
        stripped_term = term.strip()
        if category in classified and stripped_term and stripped_term not in seen_terms:
            classified[category].append(stripped_term)
            seen_terms.add(stripped_term)  # ← 重複防止
```

**コミット**:
- テスト: `71297d7` - "Add test for duplicate term deduplication in return_categories mode"
- 実装: `d7deabc` - "Implement duplicate term deduplication in batch classification"

## 検証結果

- ✅ 全テスト (461件) パス
- ✅ Pyright静的解析エラーなし
- ✅ 既存機能の後方互換性維持
- ✅ DB保存時のIntegrityError解消

## 残作業

なし。全ての計画項目が実装完了。
