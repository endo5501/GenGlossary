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

## ユーザー補足情報（user_notes）のフロー

```
ユーザー → Terms画面で user_notes 入力（auto-save, debounce 500ms）
                ↓
        PATCH /api/projects/{id}/terms/{term_id}
                ↓
        terms_extracted.user_notes に保存
                ↓
    ┌───────────────────────────────────────────┐
    │ Generate:                                 │
    │   _build_user_notes_map(term_rows)        │
    │   → プロンプトに「ユーザー補足情報」注入  │
    │   → wrap_user_data()でインジェクション防止 │
    ├───────────────────────────────────────────┤
    │ Review:                                   │
    │   provisional glossary + user_notes_map   │
    │   → プロンプトに補足情報を付記            │
    ├───────────────────────────────────────────┤
    │ Refine:                                   │
    │   issues + glossary + user_notes_map      │
    │   → 改善時に補足情報を根拠として活用      │
    └───────────────────────────────────────────┘

Extract時のuser_notes保持:
    backup_user_notes(conn) → {term_text: user_notes}
    Extract実行（terms_extracted クリア＆再作成）
    restore_user_notes(conn, backup) → term_textでマッチして復元
```

**user_notes_mapの流れ:**
- `full`スコープ: `_execute_full` → `_build_user_notes_map` → `_do_generate`/`_do_review`/`_do_refine`
- 個別スコープ: `_execute_generate`/`_execute_review`/`_execute_refine` でもそれぞれ `_build_user_notes_map` を呼び出し

## Extract の実行タイミング

用語抽出（Extract）は Full Pipeline（`scope="full"`）から除外されており、以下のタイミングで実行されます:

1. **ファイル追加時の自動実行**: `POST /api/projects/{id}/files/bulk` でファイル保存成功後に自動的に Extract が開始される（`triggered_by="auto"`）
2. **手動実行**: Terms 画面の Extract ボタン、または `scope="extract"` での Run 実行

Full Pipeline（`scope="full"`）は `generate → review → refine` のみを実行し、DB に既存の用語が存在していることを前提とします。用語が 0 件の場合はエラーになります。

```
ファイル追加フロー:
ファイル追加 → DBに保存 → Extract自動開始（バックグラウンド）
                              ↓ 既にRunが実行中の場合はスキップ
                              → extract_skipped_reason をレスポンスで通知

Full Pipeline実行フロー（scope="full"）:
DBから用語読み込み → generate → review → refine
（extractはスキップ）
```
