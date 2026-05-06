---
description: "Use when: engineering principles, DRY, Clean Architecture, SOLID, error handling, security, observability, docstrings, or comment language conventions apply. Auto-attached to all files."
applyTo: "**"
---

# Engineering Principles

## Objective
- Deliver complete, maintainable, and secure solutions.
- Prioritize clarity, consistency, and low coupling.

## DRY & simplicity
- Avoid duplicated logic — extract reusable utilities, helpers, or shared services.
- Centralize business rules in the domain/application layer.
- Avoid premature abstractions: abstract only when duplication or variability justify it.

## Clean Architecture
Separate layers with clear responsibilities:
- **Presentation / Entry** — UI, controllers, handlers. No business logic.
- **Application** — use cases, orchestration, services.
- **Domain** — pure business rules, models.
- **Infrastructure** — DB, external APIs, filesystem, queues.

Domain logic must not depend on frameworks or infrastructure details. Inject dependencies via interfaces/contracts.

## SOLID
- **SRP**: one clear reason to change per module.
- **OCP**: extend without breaking existing behavior.
- **LSP / ISP / DIP**: small contracts, explicit dependencies, invert dependencies where viable.

## Error handling & observability
- Fail fast with clear, actionable messages.
- Never swallow relevant errors or convert them to ambiguous states.
- Log useful context without exposing secrets or sensitive data.

## Security
- Validate and sanitize all external input at system boundaries.
- No hardcoded secrets — use environment variables or a secrets manager.
- Apply least privilege for DB, API, and resource access.

## Quality & testing
- Non-trivial changes must include tests appropriate to their impact.
- One behavior per test, descriptive name.
- Fix root causes, not symptoms. Avoid tests coupled to internal implementation.

## Docstrings & comments (language)
- **Docstrings** (functions, classes, modules): **English** — compatible with Sphinx, TypeDoc, JSDoc, OpenAPI.
- **Inline comments** (business logic, design decisions): **Spanish or English**, consistent with the file's prevailing language.
- Never mix languages within the same docstring or comment block.

## Conventions
- Respect existing style, structure, and patterns in the repository.
- Avoid cosmetic changes unrelated to the current task.
