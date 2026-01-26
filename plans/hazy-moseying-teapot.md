# docs/architecture.md 階層化計画

## 現状

- `docs/architecture.md`: 約2535行 / 27871トークン（巨大）
- 主なセクションと行数:
  - ディレクトリ構成: 135行
  - モジュール構成: 2076行（最大）
    - models/: 92行
    - llm/: 77行
    - db/: 435行
    - 処理レイヤー: 118行
    - output/: 8行
    - api/: 601行
    - runs/: 372行
    - CLI層: 364行
  - データフロー: 137行
  - import文の例: 61行
  - モジュール分割の判断基準: 34行
  - 依存関係の原則: 65行
  - データベース設計の原則: 16行

## 提案する構造

```
docs/
└── architecture/
    ├── README.md              # インデックス（概要＋ナビゲーション）
    ├── directory-structure.md # ディレクトリ構成
    ├── models.md              # models/ + llm/ + output/ + 処理レイヤー
    ├── database.md            # db/ - データベース層
    ├── api.md                 # api/ - FastAPI バックエンド
    ├── runs.md                # runs/ - Run管理
    ├── cli.md                 # CLI層
    ├── data-flow.md           # データフロー図
    └── design-principles.md   # import文、モジュール分割、依存関係、DB原則
```

## 各ファイルの内容と推定サイズ

| ファイル | 内容 | 推定行数 |
|---------|------|---------|
| `README.md` | 全体概要、ナビゲーションリンク | 50-80 |
| `directory-structure.md` | プロジェクトのファイル構造 | 135 |
| `models.md` | models/ + llm/ + output/ + 処理レイヤー（小規模モジュール統合） | ~300 |
| `database.md` | db/ - Schema v3、Repository、接続管理 | ~450 |
| `api.md` | api/ - FastAPI、スキーマ、ルーター、ミドルウェア | ~600 |
| `runs.md` | runs/ - RunManager、PipelineExecutor | ~380 |
| `cli.md` | CLI - メイン、DB、Project、API コマンド | ~370 |
| `data-flow.md` | データフロー図（基本、DB保存、カテゴリ分類） | ~140 |
| `design-principles.md` | import文、モジュール分割、依存関係、DB設計原則 | ~180 |

## 実装手順

### 1. ディレクトリ作成
```bash
mkdir -p docs/architecture
```

### 2. ファイル作成（順序）
1. `directory-structure.md` - 独立セクション
2. `models.md` - 基盤モデル層
3. `database.md` - DB層
4. `api.md` - API層
5. `runs.md` - Run管理
6. `cli.md` - CLI層
7. `data-flow.md` - データフロー
8. `design-principles.md` - 設計原則
9. `README.md` - インデックス（最後）

### 3. 旧ファイル削除
- 分割完了後に `docs/architecture.md` を削除

### 4. CLAUDE.md 更新
```markdown
### 詳細ドキュメント（必要時に参照）
- `docs/architecture/` - アーキテクチャガイド（README.md から各詳細へ）
```

## 対象ファイル

### 変更するファイル
- `/Users/endo5501/Work/GenGlossary/.claude/CLAUDE.md` - 参照パス更新

### 削除するファイル
- `/Users/endo5501/Work/GenGlossary/docs/architecture.md` - 分割後に削除

### 新規作成するファイル
- `/Users/endo5501/Work/GenGlossary/docs/architecture/README.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/directory-structure.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/models.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/database.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/api.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/runs.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/cli.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/data-flow.md`
- `/Users/endo5501/Work/GenGlossary/docs/architecture/design-principles.md`

## 検証方法

1. 全ファイルが作成されていることを確認
2. README.md から各ファイルへのリンクが有効か確認
3. CLAUDE.md の参照パスが正しいか確認
4. 旧 architecture.md が削除されていることを確認
