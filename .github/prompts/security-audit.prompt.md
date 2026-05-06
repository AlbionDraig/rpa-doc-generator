---
description: "Perform a security audit of a file, module, or endpoint. Checks OWASP Top 10, secrets exposure, input validation, auth/authz, and dependency vulnerabilities."
agent: ask
tools: [read, search]
argument-hint: "Archivo, módulo o endpoint a auditar (Ej: app/api/v1/auth.py, o 'toda la capa de autenticación')"
---

#file:./_engineering-principles.md

## Contexto

Audita el siguiente objetivo en busca de vulnerabilidades de seguridad:

**Objetivo**: `${input:target:Archivo o módulo a auditar}`
**Stack**: `${input:stack:Python/FastAPI, React/TypeScript u otro}`
**Alcance**: `${input:scope:auth|input-validation|deps|all}`

---

## Proceso

### 1. Exploración
Lee el objetivo completo antes de emitir cualquier juicio. Si el target es amplio, prioriza:
- Endpoints que reciben input externo.
- Lógica de autenticación y autorización.
- Acceso a base de datos o sistema de archivos.
- Manejo de tokens, contraseñas o datos sensibles.

### 2. Checklist OWASP Top 10

Evalúa cada categoría y marca su estado:

| # | Categoría | Estado |
|---|---|---|
| A01 | **Broken Access Control** — rutas sin auth, escalada de privilegios, IDOR | ✅ / ⚠️ / ❌ |
| A02 | **Cryptographic Failures** — datos sensibles en claro, cifrado débil, secrets en código | ✅ / ⚠️ / ❌ |
| A03 | **Injection** — SQL/NoSQL injection, command injection, SSTI | ✅ / ⚠️ / ❌ |
| A04 | **Insecure Design** — ausencia de rate limiting, flujos de negocio bypasseables | ✅ / ⚠️ / ❌ |
| A05 | **Security Misconfiguration** — CORS permisivo, headers faltantes, debug activo en prod | ✅ / ⚠️ / ❌ |
| A06 | **Vulnerable Components** — dependencias con CVEs conocidos | ✅ / ⚠️ / ❌ |
| A07 | **Auth & Session Failures** — tokens débiles, sin expiración, sin revocación | ✅ / ⚠️ / ❌ |
| A08 | **Integrity Failures** — deserialización insegura, dependencias sin integridad verificada | ✅ / ⚠️ / ❌ |
| A09 | **Logging & Monitoring Failures** — eventos críticos sin log, datos sensibles en logs | ✅ / ⚠️ / ❌ |
| A10 | **SSRF** — requests a URLs controladas por el usuario sin validación | ✅ / ⚠️ / ❌ |

### 3. Checks adicionales

- **Secrets hardcodeados**: busca patrones `password=`, `secret=`, `token=`, `api_key=` en código fuente.
- **Validación de entrada**: todo input externo (body, query, path params, headers) tiene esquema/validación explícita.
- **Manejo de errores**: los errores no exponen stack traces, nombres de tablas, ni rutas internas al cliente.
- **Autorización granular**: se verifica propiedad del recurso (no solo autenticación).
- **Sanitización de output**: los datos enviados al cliente están acotados a los campos necesarios (no se filtra el modelo ORM completo).

---

## Output

### Resumen ejecutivo
Una o dos frases sobre el estado general de seguridad del objetivo.

### Hallazgos

Agrupa por severidad:

#### 🔴 Crítico — exploitable con impacto alto; debe corregirse antes de merge
- **[OWASP-AXX]** Descripción del problema.
  - Ubicación: `archivo:línea`
  - Riesgo: qué puede ocurrir si se explota.
  - Corrección sugerida: acción concreta.

#### 🟡 Importante — riesgo real pero mitigable a corto plazo
(mismo formato)

#### 🔵 Sugerencia — mejora de defensa en profundidad, no bloqueante
(mismo formato)

### Sin hallazgos
Si una categoría OWASP no presenta problemas, indícalo explícitamente — no la omitas.

### Próximos pasos recomendados
Lista priorizada de acciones a tomar.
