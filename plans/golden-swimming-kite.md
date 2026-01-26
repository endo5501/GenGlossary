# Frontend コードレビュー指摘対応計画（第2ラウンド）

## 概要

第2回コードレビュー（code-simplifier + codex MCP）で指摘された High・Medium 優先度の問題を修正します。

## 対象ファイル

| ファイル | 修正内容 |
|---------|---------|
| `frontend/src/api/client.ts` | ApiError修正、falsy対応、Content-Type条件分岐 |
| `frontend/src/components/layout/GlobalTopBar.tsx` | 型ガード関数追加 |
| `frontend/src/__tests__/routing.test.tsx` | `it.each` でパラメータ化 |
| `frontend/src/__tests__/api-client.test.ts` | falsyデータテスト追加 |

---

## High 優先度

### 1. ApiError の message/detail 重複修正 (`client.ts:30`)

**問題**: `throw new ApiError(detail, response.status, detail)` で同じ値を2回渡している

**修正**:
```typescript
// Before
throw new ApiError(detail, response.status, detail)

// After
throw new ApiError(`Request failed: ${response.status}`, response.status, detail)
```

### 2. Select onChange の型ガード追加 (`GlobalTopBar.tsx`)

**問題**: `value as RunScope` が安全でない

**修正**:
```typescript
// 型ガード関数を追加
const isRunScope = (value: string): value is RunScope =>
  ['full', 'from_terms', 'provisional_to_refined'].includes(value)

// onChange を修正
onChange={(value) => {
  if (value && isRunScope(value)) {
    setScope(value)
  }
}}
```

---

## Medium 優先度

### 3. falsy データのドロップ問題 (`client.ts:69`)

**問題**: `data ? JSON.stringify(data) : undefined` で `0`, `''`, `false` がドロップされる

**修正**:
```typescript
// Before
body: data ? JSON.stringify(data) : undefined,

// After
body: data !== undefined ? JSON.stringify(data) : undefined,
```

### 4. Content-Type 固定問題 (`client.ts:44-45`)

**問題**: 常に `Content-Type: application/json` を設定するため、FormData等で問題

**修正**:
```typescript
// Before
const headers = new Headers(options.headers)
headers.set('Content-Type', 'application/json')

// After: bodyがある場合のみ、かつ既存ヘッダーがない場合のみ設定
const headers = new Headers(options.headers)
if (options.body && !headers.has('Content-Type')) {
  headers.set('Content-Type', 'application/json')
}
```

### 5. テストコードのパラメータ化 (`routing.test.tsx`)

**問題**: ルートナビゲーションテストが各ルートごとに繰り返し

**修正**: `it.each` を使用
```typescript
const navigationRoutes = [
  { path: '/files', name: /files/i },
  { path: '/terms', name: /terms/i },
  { path: '/provisional', name: /provisional/i },
  { path: '/issues', name: /issues/i },
  { path: '/refined', name: /refined/i },
  { path: '/document-viewer', name: /document/i },
  { path: '/settings', name: /settings/i },
]

it.each(navigationRoutes)('should navigate to $path', async ({ path, name }) => {
  const { router } = await renderApp()
  const user = userEvent.setup()
  await user.click(screen.getByRole('link', { name }))
  await waitFor(() => {
    expect(router.state.location.pathname).toBe(path)
  })
})
```

---

## 対応を見送る指摘（Low優先度）

以下は現時点では対応しない：
- マジックナンバー定数化（`204`, `'0'`）
- URL結合の正規化
- `statusColors` の未知の値対応
- テストヘルパーの柔軟性向上

---

## 実装順序

1. `api/client.ts` - ApiError修正、falsy対応、Content-Type条件分岐
2. `api-client.test.ts` - falsyデータのテスト追加
3. `GlobalTopBar.tsx` - 型ガード関数追加
4. `routing.test.tsx` - `it.each` でパラメータ化

---

## 検証方法

```bash
cd frontend
pnpm test      # 全テスト通過
pnpm lint      # エラーなし
pnpm build     # ビルド成功
```
