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
