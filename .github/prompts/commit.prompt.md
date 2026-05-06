---
description: "Generate a Conventional Commit message from staged changes or a description of what was done. Use before committing to ensure the message follows project conventions."
agent: ask
tools: [read, search, execute]
argument-hint: "Describe brevemente qué cambiaste, o deja vacío para que analice el diff actual"
---

## Contexto

Genera un mensaje de commit siguiendo [Conventional Commits](https://www.conventionalcommits.org/) según las convenciones del proyecto.

**Descripción del cambio** (opcional): `${input:description:Deja vacío para analizar el diff automáticamente}`

---

## Proceso

### 1. Obtener los cambios

Si no se proveyó descripción, ejecuta:

```bash
git diff --staged --stat
git diff --staged
```

Si no hay cambios staged, usa `git diff HEAD` para ver los cambios más recientes.

### 2. Analizar los cambios

Identifica:
- **Qué archivos** cambiaron y en qué capa (api, services, models, components, hooks, tests, config, docs, ci).
- **Qué tipo de cambio** es: feat / fix / chore / docs / test / refactor / perf / ci / revert.
- **Scope**: módulo, feature o área afectada (e.g., `auth`, `transactions`, `migrations`, `frontend`).
- Si hay **BREAKING CHANGE**: cambio de contrato de API, schema incompatible, rename de export público.

### 3. Generar el mensaje

Formato:

```
<type>(<scope>): <description>

[body — solo si el cambio necesita contexto adicional; explica el "por qué", no el "qué"]

[footer — BREAKING CHANGE: ..., y/o Closes #<issue> si aplica]
```

**Reglas obligatorias:**
- Subject en inglés, lowercase, modo imperativo, máximo 72 caracteres.
- Sin punto final en el subject.
- Body solo si el subject no es auto-explicativo.
- `BREAKING CHANGE:` en footer cuando el cambio rompe compatibilidad.

### 4. Output

Presenta:

1. **Mensaje de commit listo para copiar** (bloque de código).
2. **Justificación breve** del tipo y scope elegidos (1-2 líneas).
3. Si detectas múltiples objetivos desacoplados en el diff, sugiere **dividir en commits atómicos** y proporciona un mensaje por cada uno.

### 5. Verificación adicional

Revisa que el diff no incluya accidentalmente:
- Archivos `.env`, `*.pem`, `*.key`, o cualquier secreto.
- Archivos de debug temporales o `console.log` / `print` statements de desarrollo.
- Archivos no relacionados con el objetivo del commit.

Si detectas alguno, advierte al usuario antes de proporcionar el mensaje.
