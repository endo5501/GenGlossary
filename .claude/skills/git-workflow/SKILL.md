---
name: git-workflow
description: "Git workflow and commit conventions for GenGlossary project. Covers branch strategy (main, feature branches), ticket system integration (ticket.sh commands), commit message rules (Add, Implement, Fix, Refactor verbs in English), and best practices. Use when: (1) Creating or switching branches, (2) Writing commit messages, (3) Working with the ticket system (start, close tickets), (4) Reviewing commit history, (5) Needing examples of good/bad commits."
---

# Git Workflow

Git version control with ticket-based task management for GenGlossary project.

## Branch Strategy

### Main Branch
- **`main`**: Production branch, always in working state

### Feature Branches
- **`feature/<ticket-name>`**: Work branch for each ticket

### Branch Naming

```bash
# ✅ Good
feature/251231-123014-phase1-data-models-foundation
feature/251231-123015-phase2-llm-client
feature/add-glossary-export-feature

# ❌ Bad
feature/test
feature/fix
my-branch
```

## Ticket System

### Commands

```bash
# List tickets
bash scripts/ticket.sh list

# Start ticket
bash scripts/ticket.sh start <ticket-name>

# Complete ticket
bash scripts/ticket.sh close
```

### Ticket Workflow

#### 1. List Available Tickets

```bash
$ bash scripts/ticket.sh list

Available tickets:
  251231-123014-phase1-data-models-foundation
  251231-123015-phase2-llm-client
  ...
```

#### 2. Start Ticket

```bash
$ bash scripts/ticket.sh start 251231-123014-phase1-data-models-foundation

✓ Created branch: feature/251231-123014-phase1-data-models-foundation
✓ Switched to branch: feature/251231-123014-phase1-data-models-foundation
✓ Created current-ticket.md
```

What happens:
- Creates `feature/<ticket-name>` branch
- Switches to the branch automatically
- Creates `current-ticket.md` for tracking

#### 3. Develop with TDD Cycle

```bash
# Add tests first
$ git add tests/
$ git commit -m "Add Document model tests"

# Then implement
$ git add src/
$ git commit -m "Implement Document model"
```

#### 4. Complete Ticket

```bash
$ bash scripts/ticket.sh close

✓ All tests passed
✓ Merged feature/... into main
✓ Deleted feature branch
✓ Ticket completed
```

What happens:
- Runs tests (must pass)
- Merges feature branch into `main`
- Deletes feature branch
- Updates `current-ticket.md`

## Commit Message Rules

### Basic Rules

1. **Write in English**: All commit messages in English
2. **Start with verb**: "Add", "Implement", "Fix", "Refactor", etc.
3. **Use present tense**: "Add" not "Added"
4. **Be concise**: First line ≤ 50 characters
5. **Add details if needed**: Blank line, then detailed description

### Verb Usage

| Verb | Purpose | Example |
|------|---------|---------|
| **Add** | New files, features, tests | `Add Document model tests` |
| **Implement** | Feature implementation | `Implement OllamaClient` |
| **Fix** | Bug fixes | `Fix IndexError in get_line()` |
| **Refactor** | Code improvement (no behavior change) | `Refactor to reduce complexity` |
| **Update** | Update existing code | `Update dependencies to latest` |
| **Remove** | Delete code/files | `Remove deprecated method` |
| **Rename** | Rename files/variables | `Rename TermExtractor to Analyzer` |

### Good Commit Message Patterns

```bash
# Tests
"Add Document model tests"
"Add OllamaClient integration tests"
"Add TermExtractor unit tests for edge cases"

# Implementation
"Implement Document model"
"Implement OllamaClient with retry logic"
"Implement term extraction with morphological analysis"

# Bug fixes
"Fix IndexError in Document.get_line()"
"Fix JSON parsing error in OllamaClient"
"Fix incorrect term extraction for compound words"

# Refactoring
"Refactor glossary_generator to reduce complexity"
"Refactor Document model to use Pydantic validators"
"Refactor term_extractor to improve readability"

# Multi-line (with details)
"Add Document.get_context() tests

Test cases:
- Returns line with surrounding context
- Handles document start boundary
- Handles document end boundary"
```

### Bad Commit Messages

```bash
# ❌ Vague
"update code"
"fix bug"
"test"
"wip"
"done"

# ❌ Japanese (should be English)
"Document モデルを追加"

# ❌ Lowercase start
"add document model"

# ❌ Past tense
"Added Document model"
"Fixed bug"

# ❌ Not specific
"update"
"fix"
"changes"
```

## Development Flow Example

```bash
# 1. Start ticket
$ bash scripts/ticket.sh start 251231-123015-phase2-llm-client

# 2. Check current branch
$ git branch
* feature/251231-123015-phase2-llm-client
  main

# 3. TDD cycle 1
$ git add tests/llm/test_ollama_client.py
$ git commit -m "Add OllamaClient tests"

$ git add src/genglossary/llm/ollama_client.py
$ git commit -m "Implement OllamaClient"

# 4. TDD cycle 2
$ git add tests/llm/test_ollama_client.py
$ git commit -m "Add OllamaClient.generate_structured() tests"

$ git add src/genglossary/llm/ollama_client.py
$ git commit -m "Implement OllamaClient.generate_structured()"

# 5. Run all tests
$ uv run pytest
====== 10 passed in 1.23s ======

# 6. Complete ticket
$ bash scripts/ticket.sh close
```

## Good vs Bad Commit History

### ✅ Good History

```
6e807b4 Refactor glossary_reviewer.py to leverage Pydantic validation
e08ff54 Refactor glossary_refiner.py to optimize algorithm complexity
9ddddeb Refactor glossary_generator.py to reduce complexity
96e3b0f Refactor morphological_analyzer.py to reduce complexity and improve efficiency
74f4fe2 Refactor cli.py to improve readability and maintainability
```

**Why good:**
- Each commit has one clear change
- Specific commit messages
- Clear intent ("Refactor")
- States what was improved (complexity, efficiency, readability)

### ❌ Bad History

```
a1b2c3d update
d4e5f6g fix bug
h7i8j9k wip
l0m1n2o changes
p3q4r5s test
```

**Problems:**
- Unclear what changed
- Vague messages
- Cannot understand history later

## FAQ

### Q1: Incorrect Commit Message

```bash
# Fix the last commit message
$ git commit --amend -m "Correct commit message"

# Warning: Avoid if already pushed
```

### Q2: Committed Wrong Files

```bash
# Undo last commit (keep changes)
$ git reset --soft HEAD~1

# Fix files, then re-commit
$ git add <correct-files>
$ git commit -m "Correct commit message"
```

### Q3: Wrong Branch

```bash
# Check current branch
$ git branch

# Switch to correct branch
$ git checkout feature/correct-branch-name
```

### Q4: Merge Main Changes

```bash
# Get latest main
$ git checkout main
$ git pull

# Return to feature branch and merge
$ git checkout feature/your-branch
$ git merge main
```

## Detailed Examples

For comprehensive examples of good/bad commits with detailed analysis, see:

**[references/good-bad-commits.md](references/good-bad-commits.md)**

This reference includes:
- Real project commit examples
- Pattern-by-pattern breakdown (Add, Implement, Fix, Refactor, Update, Remove)
- Multi-line commit message examples
- Practical scenarios (test + implementation, multiple features, bug fixes)
- Commit message checklist
