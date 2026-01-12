---
priority: 1
tags: [enhancement, glossary, review]
description: "Filter out unnecessary terms during glossary review phase"
created_at: "2026-01-08T15:00:35Z"
started_at: 2026-01-12T06:27:48Z # Do not modify manually
closed_at: null   # Do not modify manually
---

# 用語集の精査フェーズで不要な用語をフィルタリング

## 概要

現在の用語集生成プロセスでは、抽出されたすべての用語が精査・改善されて用語集に含まれます。しかし、一般的な語彙や文脈から明らかに意味がわかる用語については、わざわざ用語集に含める必要がありません。

精査（Review）フェーズで各用語の必要性を判断し、以下のような用語を用語集から除外できるようにします：

- 一般的な語彙で説明不要なもの
- 文脈から意味が明確で補足説明が不要なもの
- 単純すぎて定義する価値がないもの

## 現状の処理フロー

```
用語抽出 → 用語集生成 → 精査 → 改善 → 出力
                        ↑
                    すべての用語が
                    そのまま通過
```

## 改善後の処理フロー

```
用語抽出 → 用語集生成 → 精査 → 改善 → 出力
                        ↑
                    各用語の必要性を判断
                    不要な用語は除外
```

## Tasks

- [x] GlossaryIssue モデルに `should_exclude` フィールドを追加
- [x] GlossaryReviewer のプロンプトを更新して、各用語の必要性判断を含める
- [x] GlossaryRefiner で `should_exclude=True` の用語を除外する処理を追加
- [x] 除外理由をログ出力またはデバッグ情報として表示
- [x] 単体テストを追加（除外ロジック、プロンプト更新）
- [x] 統合テストで除外機能の動作確認
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## 技術的詳細

### GlossaryIssue モデルの変更案

```python
class GlossaryIssue(BaseModel):
    term: str
    issue_type: str  # "unclear", "contradiction", "missing", "unnecessary"
    description: str
    should_exclude: bool = False  # True if term should be removed from glossary
    exclusion_reason: str | None = None  # Reason for exclusion
```

### 除外判断の基準（プロンプトに含める）

1. **一般常識**: 辞書的な意味で十分理解できる一般語彙
2. **文脈の明確さ**: 文章中で意味が明確に説明されている
3. **冗長性**: 他の用語と重複している、または説明済み
4. **価値判断**: 定義を追加しても読者の理解に貢献しない

## Notes

- 除外の判断はLLMに委ねるが、最終的にはユーザーが確認できるようにする
- 将来的には除外された用語のリストを出力するオプションも検討
- 厳しすぎる除外は避け、迷った場合は含める方向で判断させる
