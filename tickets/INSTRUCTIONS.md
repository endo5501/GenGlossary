# Ticket Management Instructions

Use `./scripts/ticket.sh` for ticket management.

## Working with current-ticket.md

### If current-ticket.md exists in project root
- This file is your work instruction - follow its contents
- When receiving additional instructions from users, document them in this file before proceeding
- Continue working on the active ticket

### If current-ticket.md does not exist in project root
- When receiving user requests, first ask whether to create a new ticket
- Do not start work without confirming ticket creation
- Even small requests should be tracked through the ticket system

## Create New Ticket

1. Create ticket: `./scripts/ticket.sh new feature-name`
2. Edit ticket content and description in the generated file

## Start Working on Ticket

1. Check available tickets: `./scripts/ticket.sh list` or browse tickets directory
2. Start work: `./scripts/ticket.sh start 241225-143502-feature-name`
3. Develop on feature branch (`current-ticket.md` shows active ticket)

## Closing Tickets

1. Before closing:
   - Review `current-ticket.md` content and description
   - Check all tasks in checklist are completed (mark with `[x]`)
   - Get user approval before proceeding
2. Complete: `./scripts/ticket.sh close`
