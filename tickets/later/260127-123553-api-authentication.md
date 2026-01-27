---
priority: 5
tags: [backend, security, api]
description: "Add authentication and authorization to API endpoints to prevent unauthorized access"
created_at: "2026-01-27T12:35:53Z"
started_at: null  # Do not modify manually
closed_at: null   # Do not modify manually
---

# Ticket Overview

Implement authentication and authorization for the GenGlossary API. Currently, all API endpoints are unauthenticated and accept arbitrary `doc_root` values, which poses a security risk if the service is accessible beyond localhost.

## Background

Code review identified the following security concerns:
- API endpoints have no authentication mechanism
- Arbitrary `doc_root` paths can be registered, potentially exposing sensitive filesystem locations
- No authorization checks for project access

## Tasks

- [ ] Design authentication strategy (API key, JWT, or session-based)
- [ ] Implement authentication middleware for FastAPI
- [ ] Add `doc_root` path validation (restrict to allowed base directories)
- [ ] Add authorization checks for project-level access
- [ ] Create authentication configuration in settings
- [ ] Add tests for authentication and authorization
- [ ] Update API documentation with auth requirements
- [ ] Code simplification review using code-simplifier agent
- [ ] Code review by codex MCP
- [ ] Update docs/architecture/*.md
- [ ] Run static analysis (`pyright`) before closing and pass all tests (No exceptions)
- [ ] Run tests (`uv run pytest`) before closing and pass all tests (No exceptions)
- [ ] Get developer approval before closing


## Notes

- Consider backward compatibility for local development (optional auth for localhost)
- May need environment variable or config file for allowed base directories
- Reference: `src/genglossary/api/schemas/project_schemas.py:49`, `src/genglossary/api/routers/projects.py:99`
