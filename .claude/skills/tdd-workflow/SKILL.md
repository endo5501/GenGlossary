---
name: tdd-workflow
description: Test-Driven Development (TDD) workflow enforcing Red-Green-Commit cycle. Write tests before implementation, verify test failure, commit tests, then implement to pass tests and commit implementation. Use for new feature implementation, bug fixes, refactoring, or any code changes requiring tests.
---

# TDD Workflow

## TDD Cycle (Red-Green-Commit)

### Phase 1: Red (Test → Failure → Commit)

1. **Write tests first**
   ```python
   def test_document_get_context():
       """Test getting line with context."""
       doc = Document(content="Line 1\nLine 2\nLine 3")
       context = doc.get_context(2, context_lines=1)
       assert context == ["Line 1", "Line 2", "Line 3"]
   ```

2. **Run tests and verify failure**
   ```bash
   uv run pytest tests/test_module.py -v
   # FAILED - AttributeError: 'Document' object has no attribute 'get_context'
   ```

   **IMPORTANT**: Test MUST fail with expected error. If it passes, test is incorrect or feature already exists.

3. **Commit tests only**
   ```bash
   git add tests/
   git commit -m "Add Document.get_context() tests

   Test cases:
   - Default context (1 line before/after)
   - Custom context lines
   - Boundary handling (start/end of document)"
   ```

### Phase 2: Green (Implementation → Success → Commit)

1. **Implement minimal code to pass tests**
   ```python
   def get_context(self, line_number: int, context_lines: int = 1) -> list[str]:
       """Get a line with surrounding context."""
       start = max(0, line_number - 1 - context_lines)
       end = min(self.line_count, line_number + context_lines)
       return self.lines[start:end]
   ```

2. **Run all tests and verify success**
   ```bash
   uv run pytest
   # ====== 9 passed in 0.18s ======
   ```

3. **Commit implementation only**
   ```bash
   git add src/
   git commit -m "Implement Document.get_context()

   Returns target line with surrounding context lines,
   handling document boundaries using max/min."
   ```

### Phase 3: Refactor (Optional)

Improve code quality while keeping all tests passing.

```bash
uv run pytest  # All pass
git commit -m "Refactor Document.get_context() to improve readability"
```

## Test Naming Convention

Pattern: `test_<method>_<condition>_<expected_result>()`

Examples:
- `test_get_line_valid_index()`
- `test_get_line_raises_error_for_invalid_index()`
- `test_extract_terms_returns_empty_list_for_empty_document()`

## Commit Message Patterns

**Test commits:**
```
Add <ClassName>.<method>() tests
Add <module_name> integration tests
```

**Implementation commits:**
```
Implement <ClassName>.<method>()
Implement <feature_name>
```

**Other patterns:**
```
Fix <issue> in <module>
Refactor <module> to <improvement>
```

## TDD Checklist

### Red Phase
- [ ] Wrote tests first
- [ ] Ran tests and verified failure
- [ ] Failure reason is correct (ImportError, AttributeError, etc.)
- [ ] Added tests only (`git add tests/`)
- [ ] Committed with "Add ... tests" format

### Green Phase
- [ ] Implemented minimal code to pass tests
- [ ] All tests pass
- [ ] Added implementation only (`git add src/`)
- [ ] Committed with "Implement ..." format

### Refactor Phase (if needed)
- [ ] Tests still pass after refactoring
- [ ] Committed with "Refactor ..." format

## Common Mistakes

❌ **Writing implementation before tests**
- Always write tests first

❌ **Committing tests and implementation together**
- Split into 2 commits: tests → implementation

❌ **Not verifying test failure**
- Must see Red phase before Green phase

❌ **Over-implementation**
- Follow YAGNI (You Aren't Gonna Need It)
- Only implement what tests require

## Test File Structure

```
src/genglossary/models/document.py
→ tests/models/test_document.py

src/genglossary/llm/ollama_client.py
→ tests/llm/test_ollama_client.py
```

Rule: Mirror `src/genglossary/` structure in `tests/` with `test_` prefix.

## Detailed Example

For a complete TDD cycle example with Document.get_context() implementation, see [references/tdd-cycle-example.md](references/tdd-cycle-example.md).

This example shows:
- Complete Red-Green-Commit cycle
- Boundary condition testing
- Proper commit messages
- Real implementation from GenGlossary project
