# CLI層

## cli.py (メインコマンド)
```python
import click

@click.command()
@click.argument("input_file")
@click.option("--output", "-o", default="output/glossary.md")
def main(input_file: str, output: str) -> None:
    """用語集を生成するCLIコマンド"""
    # 1. ドキュメント読み込み
    document = load_document(input_file)

    # 2. LLMクライアント初期化
    llm_client = OllamaClient()

    # 3. 用語抽出
    extractor = TermExtractor(llm_client)
    terms = extractor.extract(document)

    # 4. 用語集生成
    generator = GlossaryGenerator(llm_client)
    glossary = generator.generate(terms, document)

    # 5. 精査
    reviewer = GlossaryReviewer(llm_client)
    issues = reviewer.review(glossary)

    # 6. 改善
    refiner = GlossaryRefiner(llm_client)
    refined_glossary = refiner.refine(glossary, issues, document)

    # 7. 出力
    write_glossary(refined_glossary, output)
```

## cli_db.py (DBサブコマンド)
```python
import click

@click.group()
def db() -> None:
    """Database management commands."""
    pass

@db.command("info")
@click.option("--db-path", default="./genglossary.db")
def info(db_path: str) -> None:
    """メタデータを表示"""
    conn = get_connection(db_path)
    metadata = get_metadata(conn)
    # Rich tableで表示
    ...

@db.group()
def terms() -> None:
    """抽出用語の管理コマンド"""
    pass

@terms.command("list")
@click.option("--db-path", default="./genglossary.db")
def terms_list(db_path: str) -> None:
    """用語一覧を表示（run_id不要）"""
    conn = get_connection(db_path)
    term_list = list_all_terms(conn)
    # Rich tableで表示
    ...

# provisional, refined コマンド群も同様（run_id削除）
```

## 利用可能なDBコマンド (Schema v2)

- `genglossary db init` - DB初期化
- `genglossary db info` - メタデータ表示
- `genglossary db terms list/show/update/delete/import/regenerate` - 用語管理
- `genglossary db provisional list/show/update/regenerate` - 暫定用語集管理
- `genglossary db issues list/regenerate` - 問題点管理
- `genglossary db refined list/show/update/export-md/regenerate` - 最終用語集管理

## cli_api.py (APIサブコマンド)
```python
import click
import uvicorn

@click.group()
def api() -> None:
    """API server commands."""
    pass

@api.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
@click.option("--reload", is_flag=True)
def serve(host: str, port: int, reload: bool) -> None:
    """FastAPIサーバーを起動"""
    uvicorn.run(
        "genglossary.api.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )
```

## 利用可能なAPIコマンド

- `genglossary api serve` - FastAPIサーバー起動
- `genglossary api serve --reload` - 開発モード（自動リロード）
- `genglossary api serve --host 0.0.0.0 --port 3000` - カスタムホスト/ポート

## regenerateコマンド群

各ステップのデータを再生成するコマンド。既存データを削除してから新規生成する。

### 1. 用語抽出の再生成
```python
@terms.command("regenerate")
@click.option("--input", required=True, help="入力ディレクトリ")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def terms_regenerate(input: str, llm_provider: str, model: str | None, db_path: str):
    """ドキュメントから用語を再抽出

    処理フロー:
    1. 既存用語を全削除（delete_all_terms）
    2. ドキュメント読み込み（DocumentLoader）
    3. LLMで用語抽出（TermExtractor）
    4. DBに保存（create_term）
    """
    ...
```

### 2. 暫定用語集の再生成
```python
@provisional.command("regenerate")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def provisional_regenerate(llm_provider: str, model: str | None, db_path: str):
    """抽出済み用語から暫定用語集を再生成

    処理フロー:
    1. 既存暫定用語を全削除（delete_all_provisional）
    2. DBから用語とドキュメントを取得
    3. ドキュメントをファイルから再構築
    4. LLMで用語集生成（GlossaryGenerator）
    5. DBに保存（create_provisional_term）
    """
    ...
```

### 3. 問題点の再生成
```python
@issues.command("regenerate")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def issues_regenerate(llm_provider: str, model: str | None, db_path: str):
    """暫定用語集を精査して問題点を再生成

    処理フロー:
    1. 既存問題を全削除（delete_all_issues）
    2. DBから暫定用語集を取得
    3. Glossaryオブジェクトを再構築
    4. LLMで精査（GlossaryReviewer）
    5. DBに保存（create_issue）
    """
    ...
```

### 4. 最終用語集の再生成
```python
@refined.command("regenerate")
@click.option("--llm-provider", default="ollama")
@click.option("--model", default=None)
@click.option("--db-path", default="./genglossary.db")
def refined_regenerate(llm_provider: str, model: str | None, db_path: str):
    """問題点に基づいて用語集を改善し最終版を再生成

    処理フロー:
    1. 既存最終用語を全削除（delete_all_refined）
    2. DBから暫定用語集、問題点、ドキュメントを取得
    3. Glossary、Issue、Documentオブジェクトを再構築
    4. LLMで改善（GlossaryRefiner）
    5. DBに保存（create_refined_term）
    """
    ...
```

## オブジェクト再構築パターン

regenerateコマンドではDBから取得したデータを元のPydanticモデルに復元する必要がある。

### Document再構築
```python
documents: list[Document] = []
loader = DocumentLoader()
for doc_row in doc_rows:
    try:
        doc = loader.load_file(doc_row["file_path"])
        documents.append(doc)
    except FileNotFoundError:
        console.print(f"[yellow]警告: ファイルが見つかりません[/yellow]")
        continue
```

### Glossary再構築
```python
from genglossary.models.term import Term
glossary = Glossary()
for prov_row in provisional_rows:
    term = Term(
        name=prov_row["term_name"],
        definition=prov_row["definition"],
        confidence=prov_row["confidence"],
        occurrences=prov_row["occurrences"],  # 既にdeserialize済み
    )
    glossary.add_term(term)
```

### GlossaryIssue再構築
```python
from genglossary.models.glossary import GlossaryIssue
issues: list[GlossaryIssue] = []
for issue_row in issue_rows:
    issue = GlossaryIssue(
        term_name=issue_row["term_name"],
        issue_type=issue_row["issue_type"],
        description=issue_row["description"],
        # should_exclude/exclusion_reasonはDBに保存されていないためデフォルト値
    )
    issues.append(issue)
```
