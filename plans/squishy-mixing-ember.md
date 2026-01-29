# GUI進捗表示とログ保持改善 - 実装計画

## 概要

GUIで処理の進捗をわかりやすく表示し、ページ遷移時にログが消えない仕組みを実装する。

## 変更対象ファイル

### バックエンド
- `src/genglossary/runs/executor.py` - 進捗コールバック統合
- `src/genglossary/types.py` - TermProgressCallback 型追加

### フロントエンド
- `frontend/src/store/logStore.ts` - 新規作成（Zustand ストア）
- `frontend/src/api/hooks/useLogStream.ts` - Zustand 統合
- `frontend/src/api/types.ts` - LogMessage 型拡張
- `frontend/src/components/layout/LogPanel.tsx` - 進捗表示UI追加

### テスト
- `tests/runs/test_executor.py` - 進捗コールバックテスト追加
- `frontend/src/__tests__/logStore.test.ts` - 新規作成
- `frontend/src/__tests__/LogPanel.test.tsx` - 進捗表示テスト追加

## 実装内容

### 1. バックエンド: 進捗報告機能

**PipelineExecutor の変更:**

```python
def _create_progress_callback(
    self,
    conn: sqlite3.Connection,
    step_name: str
) -> Callable[[int, int, str], None]:
    """進捗コールバックを生成。DB更新とSSEログを同時実行。"""
    def callback(current: int, total: int, term_name: str = "") -> None:
        if self._run_id is not None:
            update_run_progress(conn, self._run_id, current, total, step_name)
        percent = int((current / total) * 100) if total > 0 else 0
        self._log("info", f"{term_name}: {percent}%",
                  step=step_name, current=current, total=total, current_term=term_name)
    return callback
```

**ログメッセージ拡張:**
```python
{
    "run_id": 1,
    "level": "info",
    "message": "量子コンピュータ: 25%",
    "step": "provisional",
    "progress_current": 5,
    "progress_total": 20,
    "current_term": "量子コンピュータ"
}
```

### 2. フロントエンド: 状態管理

**Zustand ログストア:**
```typescript
// frontend/src/store/logStore.ts
export const useLogStore = create<LogStore>((set) => ({
  logs: [],
  currentRunId: null,
  addLog: (log) => set((state) => ({
    logs: [...state.logs, log].slice(-1000)
  })),
  clearLogs: () => set({ logs: [] }),
  setCurrentRunId: (runId) => set({ currentRunId: runId }),
}))
```

**useLogStream の改修:**
- `useState` → Zustand ストア
- `runId` 変更時のみログクリア（ページ遷移では保持）

### 3. フロントエンド: UI改善

**LogPanel 進捗表示:**
- プログレスバー追加
- 現在のステップ名表示
- 処理中の用語名表示

## 実装順序（TDD）

1. **Phase 1: バックエンド進捗更新**
   - [ ] `_create_progress_callback` テスト作成
   - [ ] `_create_progress_callback` 実装
   - [ ] `_log()` 拡張テスト・実装

2. **Phase 2: コンポーネント統合**
   - [ ] `_execute_from_terms` で callback 生成・渡し
   - [ ] GlossaryGenerator/Refiner への適用

3. **Phase 3: フロントエンド状態管理**
   - [ ] Zustand 追加（`pnpm add zustand`）
   - [ ] `logStore` テスト・実装
   - [ ] `useLogStream` 改修

4. **Phase 4: UI改善**
   - [ ] `LogMessage` 型拡張
   - [ ] `LogPanel` 進捗表示テスト・実装

## 検証方法

1. **バックエンド検証:**
   ```bash
   uv run pytest tests/runs/test_executor.py -v
   uv run pyright
   ```

2. **フロントエンド検証:**
   ```bash
   cd frontend && pnpm test
   ```

3. **E2E検証（Playwright MCP）:**
   - プロジェクト作成 → ファイル追加 → 解析実行
   - ログパネルに進捗率と処理中の用語が表示されることを確認
   - ページ遷移後もログが保持されることを確認

## リスク対策

| リスク | 対策 |
|--------|------|
| DB更新頻度が高い | 10用語ごとにバッチ更新を検討 |
| LogMessage 型互換性 | 新フィールドは全てオプショナル |
| Zustand 依存追加 | 軽量（~1KB）、React Query と共存可能 |
