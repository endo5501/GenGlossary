---
priority: 5
tags: [phase5, integration-testing, e2e, validation]
description: "Implement integration tests and end-to-end validation of the complete glossary generation pipeline"
created_at: "2025-12-31T12:30:16Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Phase 5: 統合テストとE2E検証

## 概要

全コンポーネントを統合し、エンドツーエンドでの動作確認を行います。実際のユースケースで用語集生成が正しく機能することを検証します。

## 実装対象

### テストと検証
- `tests/test_integration.py` - 統合テスト
- `tests/conftest.py` - pytest フィクスチャ
- `target_docs/` - サンプルドキュメント
- ドキュメント（README.md等）

## Tasks

### conftest.py フィクスチャ（TDDサイクル1）
- [ ] `tests/conftest.py` 作成
  - `sample_documents` フィクスチャ（テスト用ドキュメント）
  - `mock_llm_client` フィクスチャ（モック化されたLLM）
  - `sample_glossary` フィクスチャ（テスト用Glossary）
  - `tmp_path_with_docs` フィクスチャ（一時ディレクトリ + サンプル）
- [ ] コミット

### 統合テスト（TDDサイクル2）
- [ ] `tests/test_integration.py` 作成
  - 全パイプラインのモック統合テスト
    - DocumentLoader → TermExtractor → GlossaryGenerator → GlossaryReviewer → GlossaryRefiner → MarkdownWriter
  - エラーハンドリングの統合テスト
  - 空ドキュメントのハンドリング
  - 大量ドキュメントの処理
- [ ] テスト実行 → 失敗確認
- [ ] コミット（テストのみ）
- [ ] 必要に応じてコンポーネント修正
- [ ] テストパス確認
- [ ] コミット（修正）

### 実Ollama統合テスト（オプション）
- [ ] `tests/test_ollama_integration.py` 作成
  - `@pytest.mark.skipif` でOllama未起動時はスキップ
  - 実際のOllamaサーバーを使用した動作確認
  - 小さなサンプルドキュメントで検証
- [ ] 実行確認（Ollama起動時のみ）
- [ ] コミット

### サンプルドキュメント作成
- [ ] `target_docs/sample_architecture.md` 作成
  - アーキテクチャに関する技術文書サンプル
  - 複数の専門用語を含む
- [ ] `target_docs/sample_glossary_terms.txt` 作成
  - テキスト形式のサンプル
- [ ] コミット

### E2Eテスト
- [ ] Ollamaサーバー起動
- [ ] `uv run genglossary generate --input ./target_docs --output ./output/glossary.md` 実行
- [ ] 生成された用語集の確認
  - 用語が正しく抽出されているか
  - 定義が適切か
  - 出現箇所が正しく記載されているか
  - 関連用語リンクが機能しているか
- [ ] 問題があればプロンプトや実装を調整
- [ ] 再度E2Eテスト
- [ ] コミット

### ドキュメント整備
- [ ] README.md 作成
  - プロジェクト概要
  - インストール手順
  - 使用方法
  - 設定方法
  - トラブルシューティング
- [ ] `.env.example` の確認
- [ ] コミット

### 最終確認
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] カバレッジ確認（目標: 80%以上）
- [ ] 全Phase（1-5）の動作確認
- [ ] Get developer approval before closing


## Notes

### 統合テストの構成

```python
# tests/test_integration.py
import pytest
from genglossary.document_loader import DocumentLoader
from genglossary.term_extractor import TermExtractor
from genglossary.glossary_generator import GlossaryGenerator
from genglossary.glossary_reviewer import GlossaryReviewer
from genglossary.glossary_refiner import GlossaryRefiner
from genglossary.output.markdown_writer import MarkdownWriter

def test_end_to_end_glossary_generation(tmp_path, mock_llm_client):
    """全パイプラインの統合テスト（LLMはモック）"""
    # 1. ドキュメント読み込み
    loader = DocumentLoader(tmp_path)
    documents = loader.load_documents()

    # 2. 用語抽出
    extractor = TermExtractor(mock_llm_client)
    terms = extractor.extract_terms(documents)

    # 3. 用語集生成
    generator = GlossaryGenerator(mock_llm_client)
    glossary = generator.generate(documents, terms)

    # 4. 精査
    reviewer = GlossaryReviewer(mock_llm_client)
    issues = reviewer.review(glossary)

    # 5. 改善
    refiner = GlossaryRefiner(mock_llm_client)
    refined_glossary = refiner.refine(glossary, issues, documents)

    # 6. Markdown出力
    writer = MarkdownWriter()
    output_path = tmp_path / "glossary.md"
    writer.write(refined_glossary, output_path)

    # 検証
    assert output_path.exists()
    content = output_path.read_text()
    assert "# 用語集" in content
    assert len(refined_glossary.terms) > 0

@pytest.mark.skipif(not ollama_available(), reason="Ollama not running")
def test_real_ollama_integration():
    """実際のOllamaサーバーを使用したテスト"""
    # 実装...
```

### サンプルドキュメントの内容

**target_docs/sample_architecture.md**:
```markdown
# システムアーキテクチャ

## 概要

本システムはマイクロサービスアーキテクチャを採用しています。
各コンポーネントは独立してデプロイ可能で、APIゲートウェイを
介して通信します。

## コンポーネント

### APIゲートウェイ
すべてのリクエストの入り口となるコンポーネントです。
認証、ルーティング、レート制限を担当します。

### データベース
PostgreSQLを使用し、トランザクション整合性を保証します。
```

### README.md の構成

```markdown
# GenGlossary

AIを活用した用語集自動生成ツール

## 概要
...

## インストール

uv sync

## 使用方法

genglossary generate --input ./target_docs --output ./output/glossary.md

## 設定

.env ファイルを作成し、以下の環境変数を設定:
...

## 開発

pytest でテスト実行
pyright で静的解析

## トラブルシューティング
...
```

### ファイルパス
- テスト: `/Users/endo5501/Work/GenGlossary/tests/`
- サンプル: `/Users/endo5501/Work/GenGlossary/target_docs/`
- README: `/Users/endo5501/Work/GenGlossary/README.md`

### 参考
- 実装計画: `/Users/endo5501/.claude/plans/frolicking-humming-candy.md`
