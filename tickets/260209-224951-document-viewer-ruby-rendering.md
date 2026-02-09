---
priority: 3
tags: [bug, frontend, document-viewer, markdown]
description: "DocumentViewerでmdファイル内のrubyタグ（ルビ/振り仮名）が文字列として表示される問題を修正"
created_at: "2026-02-09T22:49:51Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# DocumentViewerでrubyタグ（ルビ）を正しくレンダリングする

## 問題

DocumentViewerでマークダウンファイルを表示する際、HTML形式の`<ruby>`タグが**プレーンテキストとしてそのまま表示**されてしまい、ルビ（振り仮名）が正しくレンダリングされない。

### 再現手順

以下のような記述を含むmdファイルをDocumentViewerで開く：

```html
<ruby><rb>氷川夏乃</rb><rp>（</rp><rt>ひかわなつの</rt><rp>）</rp></ruby>
```

### 期待する表示

「氷川夏乃」の上に小さく「ひかわなつの」とルビが表示される

### 実際の表示

`<ruby><rb>氷川夏乃</rb><rp>（</rp><rt>ひかわなつの</rt><rp>）</rp></ruby>` がそのまま文字列として表示される

## 原因

`DocumentPane.tsx` でドキュメントコンテンツを**プレーンテキスト**として表示しているため。

- `DocumentPane.tsx:51-88` の `renderHighlightedContent` 関数で、テキストを `<Text>` や `<span>` に直接埋め込んでいる
- ReactはデフォルトでXSS対策としてHTMLタグをエスケープする
- マークダウンパーサーやHTMLレンダリング機能は未導入（`react-markdown`等のライブラリなし）

```tsx
// 現在の実装（DocumentPane.tsx:51-54）
const renderHighlightedContent = (text: string) => {
  if (!termPattern) {
    return <Text style={{ whiteSpace: 'pre-wrap' }}>{text}</Text>  // ← エスケープされる
  }
  // ...
  return <span key={index}>{part}</span>  // ← エスケープされる
}
```

## 改善方針

`<ruby>`タグを含むHTMLを安全にレンダリングできるようにする。

### 考えられるアプローチ

1. **HTMLサニタイズ + dangerouslySetInnerHTML**
   - `DOMPurify`等でサニタイズしてから`dangerouslySetInnerHTML`でレンダリング
   - 許可するタグを`<ruby>`, `<rb>`, `<rt>`, `<rp>`に限定
   - 既存のハイライト処理との統合が課題

2. **HTMLパーサーライブラリの導入**
   - `html-react-parser` 等を使い、安全にHTMLをReactコンポーネントに変換
   - 許可タグのホワイトリスト制御が可能
   - ハイライト処理との統合がしやすい

3. **マークダウンパーサーの導入**（将来的な拡張）
   - `react-markdown` + `rehype-raw` で Markdown + HTML をレンダリング
   - より広範なマークダウン対応が可能だが、スコープが大きくなる

### ハイライト処理との統合

現在のハイライト処理（正規表現でテキストを分割し`<span>`でラップ）は、プレーンテキスト前提で動作している。rubyタグのレンダリングとの共存には以下を考慮する必要がある：

- rubyタグ内のテキスト（`<rb>`の中身）に対してもハイライトが適用されるべきか
- HTMLタグ自体がハイライトの正規表現に干渉しないか
- テキスト分割時にHTMLタグの構造を壊さないか

## 関連ファイル

- `frontend/src/components/document-viewer/DocumentPane.tsx` - ドキュメント表示+ハイライト（主な変更対象）
- `frontend/src/pages/DocumentViewerPage.tsx` - DocumentViewerページ
- `frontend/package.json` - ライブラリ追加が必要な場合

## Tasks

- [ ] 調査：ハイライト処理とHTMLレンダリングの共存方法を検討
- [ ] 設計：採用するアプローチの決定（サニタイズ方式 or パーサー方式）
- [ ] 設計：許可するHTMLタグのホワイトリスト定義
- [ ] 実装：rubyタグのレンダリング対応
- [ ] 実装：既存ハイライト処理との統合
- [ ] テスト：rubyタグが正しくレンダリングされることを確認
- [ ] テスト：rubyタグ内テキストに対するハイライト動作の確認
- [ ] テスト：XSS等セキュリティ上の問題がないことを確認
- [ ] テスト：rubyタグを含まないドキュメントの表示が壊れないこと
- [ ] Commit
- [ ] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [ ] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [ ] Update docs (glob: "*.md" in ./docs/architecture)
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing

## Notes

- GenGlossaryは小説やドキュメントの用語集を生成するツールであり、日本語の小説ではルビ表記が頻出する。この対応は実用上重要
- セキュリティ：`dangerouslySetInnerHTML`を使う場合は必ずサニタイズが必要。許可タグは最小限（`ruby`, `rb`, `rt`, `rp`）に制限すべき
- 将来的にマークダウンの見出しやリストなどもレンダリングしたい場合は、`react-markdown`導入を別チケットで検討
- 前のチケット（`term-context-viewer-with-highlight`）で新しいドキュメント表示UIを作る際にも、同じrubyレンダリング対応が必要になる
