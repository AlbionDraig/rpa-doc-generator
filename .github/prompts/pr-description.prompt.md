---
description: "Generate a Pull Request description following the project's PR template. Use before opening a PR to ensure the description includes problem, approach, risks, test evidence, and the required checklist."
agent: ask
tools: [read, search, execute]
argument-hint: "Describe brevemente el objetivo del PR, o deja vacío para que analice el diff con main/develop"
---

## Contexto

Genera una descripción completa para un Pull Request siguiendo el formato requerido en [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

**Objetivo del PR** (opcional): `${input:objective:Deja vacío para analizar el diff automáticamente}`
**Rama base**: `${input:base_branch:develop}`

---

## Proceso

### 1. Obtener los cambios

Ejecuta:

```bash
git diff ${input:base_branch:develop}...HEAD --stat
git log ${input:base_branch:develop}...HEAD --oneline
```

Si se proporcionó un objetivo, úsalo como guía. Si no, infiere el objetivo desde los commits y archivos modificados.

### 2. Analizar el impacto

Identifica:
- **Tipo de cambio**: feat / fix / refactor / chore / docs / ci / test.
- **Capas afectadas**: API, services, models, schemas, migrations, components, hooks, CI.
- **Riesgos**: ¿rompe compatibilidad de API? ¿incluye migración Alembic? ¿afecta auth? ¿cambia contratos de tipos?
- **Evidencia disponible**: tests que pasan, cobertura, screenshots si hay cambios UI.

### 3. Generar la descripción

Usa exactamente este formato:

---

## Problema

<!-- Qué problema resuelve este PR. Una o dos frases. -->

## Enfoque

<!-- Qué se hizo y por qué este enfoque. Alternativas descartadas si aplica. -->

## Riesgos e impacto

<!-- Migraciones, cambios de contrato, impacto en performance, rollback plan si aplica. -->
<!-- Si no hay riesgos relevantes, escribe "Sin riesgos identificados." -->

## Evidencia

<!-- Salida de tests, cobertura, curl de API, screenshot de UI. -->

## Checklist

- [ ] Lint OK (backend + frontend)
- [ ] Tests + cobertura OK
- [ ] Migración Alembic incluida (si aplica)
- [ ] Strings nuevos en `i18n` (`es` + `en`) (si aplica)
- [ ] CHANGELOG.md actualizado en `[Unreleased]`

---

### 4. Verificaciones adicionales

Advierte si el diff incluye:
- Archivos `.env`, secretos o credenciales hardcodeadas.
- Cambios en `backend/alembic/versions/` sin que el checklist de migración esté marcado.
- Strings visibles en componentes sin su entrada en `i18n/locales/`.
- `console.log` / `print` statements de debug que no deberían llegar a producción.
