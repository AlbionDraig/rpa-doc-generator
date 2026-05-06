---
description: "Use when writing React components, TypeScript hooks, pages, or Tailwind CSS styles in the frontend. Covers component architecture, data fetching patterns, design system tokens, and accessibility rules."
applyTo: "frontend/src/**/*.{ts,tsx}"
---

# Frontend (React / TypeScript / Tailwind) Guidelines

## Architecture layers
- `src/pages/` — Layout and composition; delegate fetching to hooks.
- `src/components/` — Reusable presentational components; no business logic.
- `src/hooks/` — Data fetching with React Query (`useQuery` / `useMutation`).
- `src/store/` — Global client state only; never fetch remote data here.
- `src/api/` — Typed HTTP client wrappers; never call `fetch`/`axios` directly in components.

## Component rules
- Props typed with explicit `interface` or `type`.
- Always implement loading / error / empty states for data-driven views.
- Extract repeated UI into sub-components.
- No API calls, store writes, or business logic in presentational components.

## Data fetching (React Query)
- `queryKey` must include every param that affects the result.
- Set `staleTime` appropriate to the data's freshness requirements.
- Mutations: call `queryClient.invalidateQueries` for all affected keys on success.

## Design system (Tailwind tokens — `tailwind.config.js`)
- Brand: `bg-brand`, `text-brand`, `bg-brand-hover`, `bg-brand-light`, `text-brand-text`
- Success: `text-success`, `bg-success-bg`, `text-success-text`
- Warning: `text-warning`, `bg-warning-bg`, `text-warning-text`
- Neutrals: `neutral-900`, `neutral-700`, `neutral-400`, `neutral-100`, `neutral-50`
- Typography: only `font-normal` and `font-medium` — never `font-bold` or `font-semibold`.
- Never use default Tailwind color scales (`red-500`, `green-600`, etc.).

## Accessibility
- Use semantic HTML elements (`button`, `nav`, `main`, `section`).
- Interactive elements must be keyboard-reachable with visible focus.
- Form inputs require associated `<label>` or `aria-label`.

## Docstrings & comments
- JSDoc/TSDoc on exported functions, hooks, and components: **English**.
- Inline comments explaining business logic or non-obvious behavior: **Spanish or English**, consistent with the file's prevailing language.
- Never mix languages within the same JSDoc block or comment.

## Tests
- Runner: `pnpm vitest run --coverage`
- E2E: `pnpm playwright test` (located in `e2e/`)
