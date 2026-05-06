---
agent: 'agent'
description: 'Analiza un traceback y propone el fix con contexto del proyecto'
tools: [read, search, edit, execute]
argument-hint: "Pega el traceback o describe el error"
---

Analiza el error y aplica el fix de causa raíz.

#file:./_engineering-principles.md

Pega el traceback o mensaje de error: ${input:error:Pega aquí el error completo}
Comando que falla (si aplica): ${input:command:Ej: npm test, pytest -q, pnpm build, docker compose up}

Pasos:
1. Identifica el origen real del error (no solo el punto donde explota).
2. Abre archivos relacionados y confirma hipótesis con evidencia del código.
3. Explica causa raíz en una oración clara.
4. Señala línea/bloque problemático.
5. Aplica fix mínimo, seguro y consistente con arquitectura del proyecto.
6. Busca patrones similares para prevenir reincidencia.

Contexto adicional si lo tienes: ${input:context:Ej: Ocurre solo cuando el usuario no tiene transacciones, o "ninguno"}

Validación:
- Ejecuta prueba específica o comando que reproduce el fallo.
- Si no existe test de regresión, crea uno.
- Reporta resultado antes/después.
