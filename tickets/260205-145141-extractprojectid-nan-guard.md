---
priority: 4
tags: [edge-case, frontend]
description: "Add NaN guard to extractProjectId in AppShell"
created_at: "2026-02-05T14:51:41Z"
started_at: 2026-02-09T14:11:58Z # Do not modify manually
closed_at: 2026-02-09T14:20:41Z # Do not modify manually
---

# Add NaN guard to extractProjectId

## 概要

`AppShell.tsx`の`extractProjectId`関数が非数値セグメントに対して予期しない値を返す可能性がある。`Number.isFinite()`ガードを追加して堅牢性を向上させる。

## 問題の詳細

```typescript
function extractProjectId(pathname: string): number | undefined {
  const match = pathname.match(/^\/projects\/(\d+)/)
  return match ? Number(match[1]) : undefined
}
```

現在の正規表現は`\d+`で数字のみをマッチするため、`/projects/foo`は`undefined`を返す。
`/projects/123abc`のようなケースでは`123`がマッチし正常に動作する。

より厳密なガードとして：
- `Number.isFinite(projectId)`でNaNやInfinityをフィルタする
- または正規表現をより厳密にする

## 関連

codex MCPのコードレビューで指摘された問題。

## Tasks

- [x] `extractProjectId`または`hasProject`で`Number.isFinite()`ガードを追加
- [x] テストの追加
- [x] Commit
- [x] Run static analysis (`pyright`) before reviwing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before reviwing and pass all tests (No exceptions)
- [x] Code simplification review using code-simplifier agent. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Code review by codex MCP. If the issue is not addressed immediately, create a ticket using "ticket" skill.
- [x] Update docs (glob: "*.md" in ./docs/architecture)
- [x] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [x] Run tests (`uv run pytest` & `pnpm test`) before closing and pass all tests (No exceptions)
- [x] Get developer approval before closing


## Notes

- 低優先度のエッジケース対応
- 現在の正規表現で大部分のケースはカバーされている
