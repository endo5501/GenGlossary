---
name: ticket
description: "Git-based ticket management system using scripts/ticket.sh. Manages tickets through markdown files with YAML frontmatter and Git branches. Use when: (1) Managing development tasks and tickets, (2) Creating, starting, or closing tickets, (3) Listing or checking ticket status, (4) Working with current-ticket.md in the project, (5) Coordinating work through Git-based ticket workflow. Automatically displays current ticket content when invoked without arguments."
---

# Ticket Management System

## Overview

This skill integrates with the Git-based ticket management system (`scripts/ticket.sh`) to manage development tasks. Each ticket is a Markdown file with YAML frontmatter, linked to Git branches for clean workflow management.

## Quick Start

**Display current ticket or list:**
```
/ticket
```
- If `current-ticket.md` exists → displays its content
- Otherwise → shows list of available tickets

**Create and start working on a ticket:**
```
/ticket new feature-name
/ticket start 250101-123456-feature-name
```

**Complete current ticket:**
```
/ticket close
```

## Core Operations

### No Arguments: Smart Display

When invoked without arguments, automatically:
1. Check if `current-ticket.md` exists and is readable
2. If yes → display ticket content to show current work
3. If no → run `bash scripts/ticket.sh list` to show available tickets

**Implementation:**
```bash
# Check for current ticket
if [ -f "current-ticket.md" ] && [ -r "current-ticket.md" ]; then
    # Display current ticket content
    cat current-ticket.md
else
    # List available tickets
    bash scripts/ticket.sh list
fi
```

### Create New Ticket: `new <slug>`

Creates a new ticket file with timestamp prefix.

**Usage:**
```
/ticket new implement-auth
/ticket new fix-bug-123
```

**Slug requirements:**
- Lowercase letters (a-z)
- Numbers (0-9)
- Hyphens (-) only

**What happens:**
1. Generates ticket file: `tickets/YYMMDD-HHMMSS-<slug>.md`
2. Creates YAML frontmatter with metadata
3. Adds default content template
4. Ready to edit before starting work

**After creation:**
- Display success message
- Remind user to edit ticket content
- Show command to start work: `bash scripts/ticket.sh start <ticket-name>`

### Start Working: `start <ticket-name>`

Begins work on a ticket by creating/switching to feature branch.

**Usage:**
```
/ticket start 250101-123456-implement-auth
```

**What happens:**
1. Updates ticket's `started_at` timestamp
2. Creates feature branch: `feature/<ticket-name>`
3. Creates `current-ticket.md` symlink to ticket file
4. Checks out the feature branch

**After starting:**
- Automatically display `current-ticket.md` content
- Show current branch and ticket information

### List Tickets: `list [options]`

Shows available tickets with filters.

**Usage:**
```
/ticket list
/ticket list --status todo
/ticket list --status doing
/ticket list --status done
/ticket list --count 10
```

**Status values:**
- `todo` - Not started (started_at: null)
- `doing` - In progress (started_at set, closed_at: null)
- `done` - Completed (closed_at set)

**Default behavior:**
- Shows `todo` and `doing` tickets only
- Sorted by status (doing first, then todo), then by priority
- Limit: 20 tickets

### Close Ticket: `close [options]`

Completes current ticket and merges to default branch.

**Usage:**
```
/ticket close
/ticket close --no-push
/ticket close --force
```

**What happens:**
1. Merges feature branch to default branch (--no-ff)
2. Moves ticket file to `tickets/done/`
3. Updates ticket's `closed_at` timestamp
4. Optionally pushes to remote (based on config)
5. Removes `current-ticket.md` symlink

**Options:**
- `--no-push` - Skip pushing to remote
- `--force` or `-f` - Force close even with uncommitted changes
- `--no-delete-remote` - Keep remote feature branch

**After closing:**
- Display completion message
- Show next steps or available tickets

## Additional Commands

### Check Status: `check`

Verifies current directory and ticket/branch synchronization.

**Usage:**
```
/ticket check
```

**Shows:**
- Current branch name
- Current ticket status
- Synchronization state between ticket and branch
- Any mismatches or issues

### Restore Link: `restore`

Restores `current-ticket.md` symlink from current branch name.

**Usage:**
```
/ticket restore
```

**When to use:**
- After cloning repository
- After pulling changes
- When `current-ticket.md` is missing

### Initialize System: `init`

Sets up ticket system in current repository.

**Usage:**
```
/ticket init
```

**What happens:**
1. Creates `.ticket-config.yaml` configuration file
2. Creates `tickets/` directory
3. Updates `.gitignore` to exclude `current-ticket.md`
4. Sets up default configuration

**When to use:**
- First time setup in new repository
- Reinitialize after config changes

## Command Routing

All commands are routed to `bash scripts/ticket.sh <args>`:

**General pattern:**
```bash
bash scripts/ticket.sh <command> [arguments]
```

**Error handling:**
- Display command output as-is
- If command fails, show error message
- Suggest corrective actions based on error type

**Output preservation:**
- Show all git command outputs for transparency
- Preserve ticket.sh messages and formatting
- Keep timestamps and status information

## Response Language

When responding to Japanese users:
- Provide explanations and guidance in Japanese
- Keep command outputs in their original form (English)
- Show ticket.sh messages without translation
- Translate only Claude's own commentary and suggestions

## Common Workflows

### Starting New Work

```
# Create ticket
/ticket new implement-login

# Edit ticket file (user does this manually)
# Then start work
/ticket start 250101-123456-implement-login

# Current ticket is now displayed automatically
```

### Checking Progress

```
# Show current ticket
/ticket

# Check status
/ticket check

# List all active tickets
/ticket list
```

### Completing Work

```
# Before closing, verify ticket content
/ticket

# Close ticket
/ticket close

# System automatically:
# - Merges to main branch
# - Moves ticket to done/
# - Removes current-ticket.md
```

### After Repository Clone

```
# Restore current ticket link
/ticket restore

# Or check what's available
/ticket list
```

## Error Scenarios

**Uncommitted changes:**
- Error: "Working directory has uncommitted changes"
- Solution: Commit or stash changes first

**Ticket not found:**
- Error: "Ticket not found"
- Solution: Run `/ticket list` to see available tickets

**Not on feature branch:**
- Error: "Not on a feature branch"
- Solution: Use `/ticket start <ticket-name>` to begin work

**Branch mismatch:**
- Error: "Ticket file and branch mismatch"
- Solution: Use `/ticket restore` or switch to correct branch
