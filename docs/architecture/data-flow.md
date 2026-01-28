# データフロー

## 基本フロー (Markdown出力のみ、DBなし)

```
┌──────────────────┐
│  target_docs/    │ 入力ドキュメント
│  sample.txt      │
└────────┬─────────┘
         │ load_document()
         ↓
┌──────────────────┐
│    Document      │ ドキュメントモデル
└────────┬─────────┘
         │ extract_terms(return_categories=False)
         ↓
┌──────────────────┐
│   List[str]      │ 用語リスト (common_noun除外済み)
└────────┬─────────┘
         │ generate()
         ↓
┌──────────────────┐
│    Glossary      │ 暫定用語集
│  (provisional)   │
└────────┬─────────┘
         │ review()
         ↓
┌──────────────────┐
│ List[Issue]      │ 問題点リスト
└────────┬─────────┘
         │ refine()
         ↓
┌──────────────────┐
│    Glossary      │ 最終用語集
│   (refined)      │
└────────┬─────────┘
         │ write_glossary()
         ↓
┌──────────────────┐
│   output/        │ 出力ファイル
│   glossary.md    │
└──────────────────┘
```

## DB保存付きフロー (デフォルト、Schema v4)

```
┌──────────────────┐     ┌──────────────────┐
│  target_docs/    │────→│ DB: metadata     │
│  sample.txt      │     │  (id=1, input_   │
└────────┬─────────┘     │   path, llm_*)   │
         │                └──────────────────┘
         │ load_document()
         ↓
┌──────────────────┐     ┌──────────────────┐
│    Document      │────→│ DB: documents    │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ extract(return_categories=True)
         ↓
┌──────────────────┐     ┌──────────────────┐
│List[Classified   │────→│ DB: terms_       │
│    Term]         │     │     extracted    │
│ (カテゴリ付き)   │     │  + category列    │
│ ※common_noun含む │     │  (run_id削除)    │
└────────┬─────────┘     └──────────────────┘
         │ generate(skip_common_nouns=True)
         ↓             ※common_nounをスキップ
┌──────────────────┐     ┌──────────────────┐
│    Glossary      │────→│ DB: glossary_    │
│  (provisional)   │     │     provisional  │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ review()
         ↓
┌──────────────────┐     ┌──────────────────┐
│ List[Issue]      │────→│ DB: glossary_    │
│  問題点リスト    │     │     issues       │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ refine()
         ↓
┌──────────────────┐     ┌──────────────────┐
│    Glossary      │────→│ DB: glossary_    │
│   (refined)      │     │     refined      │
└────────┬─────────┘     │  (run_id削除)    │
         │                └──────────────────┘
         │ write_glossary()
         ↓
┌──────────────────┐
│   output/        │ Markdown出力
│   glossary.md    │
└──────────────────┘

         ↓ DB CLIで操作可能（run_id不要）
┌──────────────────┐
│ genglossary db   │
│ - info           │
│ - terms list     │
│ - provisional    │
│ - refined        │
│   export-md      │
└──────────────────┘
```

## カテゴリ分類フロー (TermExtractor内部処理)

用語抽出は2段階のLLM処理で行われます：

```
1. SudachiPy形態素解析
   ↓ 固有名詞・複合名詞を抽出

2. LLM分類 (バッチ処理)
   ↓ 6カテゴリに分類

   - person_name (人名)
   - place_name (地名)
   - organization (組織・団体)
   - title (役職・称号)
   - technical_term (専門用語)
   - common_noun (一般名詞) ← 除外対象

3. 結果の返却
   - return_categories=False: common_noun除外 → list[str]
   - return_categories=True: 全カテゴリ含む → list[ClassifiedTerm]
```

**DB保存時の動作:**
- `return_categories=True` でカテゴリ付き抽出
- 全カテゴリ（common_noun含む）をDBの `terms_extracted` テーブルに保存
- 用語集生成時に `skip_common_nouns=True` で common_noun をフィルタ
- 既存データ（category=NULL）は common_noun として扱う

**後方互換性:**
- DBなしモード: `return_categories=False` で既存動作を維持
- 既存の `list[str]` を期待するコードはそのまま動作
